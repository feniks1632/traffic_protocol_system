from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Protocol, Vehicle, Model, Brand, Color, Owner
from backend.schemas import VehicleBase, VehicleOut, ModelOut, ColorOut, VehicleUpdate
from backend.security import check_role

router = APIRouter(tags=["vehicles"])


@router.get("", response_model=list[VehicleOut])
def get_vehicles(db: Session = Depends(get_db)):
    vehicles = db.query(Vehicle).all()
    result = []
    for v in vehicles:
        result.append(
            {
                "id": v.id,  # ← Добавляем ID
                "state_number": v.state_number,
                "model": f"{v.model.name} ({v.model.brand.name})",
                "color": v.color.name,
                "owner": f"{v.owner.last_name} {v.owner.first_name}",
                "version": v.version,
            }
        )
    return result


@router.post("", status_code=201)
def add_vehicle(data: VehicleBase, db: Session = Depends(get_db)):
    check_role(db, data.user, ["admin", "inspector"])

    exists = db.query(Vehicle).filter_by(state_number=data.state_number).first()
    if exists:
        raise HTTPException(status_code=409, detail="ТС уже существует")

    model = (
        db.query(Model)
        .join(Brand)
        .filter(Model.name == data.model_name, Brand.name == data.brand_name)
        .first()
    )
    color = db.query(Color).filter_by(name=data.color_name).first()
    owner = (
        db.query(Owner)
        .filter_by(last_name=data.owner_last_name, first_name=data.owner_first_name)
        .first()
    )

    if not all([model, color, owner]):
        raise HTTPException(status_code=400, detail="Некорректные данные")

    vehicle = Vehicle(
        state_number=data.state_number,
        model_id=model.id,
        color_id=color.id,
        owner_id=owner.id,
    )
    db.add(vehicle)
    db.commit()
    return {"status": "ok"}


@router.get("/models", response_model=list[ModelOut])
def get_models(db: Session = Depends(get_db)):
    models = db.query(Model).join(Brand).all()
    return [{"id": m.id, "name": m.name, "brand": m.brand.name} for m in models]


@router.get("/colors", response_model=list[ColorOut])
def get_colors(db: Session = Depends(get_db)):
    return db.query(Color).all()


@router.get("/{vehicle_id}", response_model=VehicleOut)
def get_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="ТС не найдено")

    return {
        "id": vehicle.id,
        "state_number": vehicle.state_number,
        "model": f"{vehicle.model.name} ({vehicle.model.brand.name})",
        "color": vehicle.color.name,
        "owner": f"{vehicle.owner.last_name} {vehicle.owner.first_name}",
        "version": vehicle.version,
    }


@router.post("/lock/{vehicle_id}")
def lock_vehicle(vehicle_id: int, user: str, db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="ТС не найдено")

    if vehicle.locked_by and vehicle.locked_by != user:
        raise HTTPException(
            status_code=409, detail="ТС уже редактируется другим пользователем"
        )

    vehicle.locked_by = user
    vehicle.locked_at = datetime.utcnow()
    db.commit()
    return {"status": "locked"}


# Разблокировка по ID
@router.post("/unlock/{vehicle_id}")
def unlock_vehicle(vehicle_id: int, user: str, db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="ТС не найдено")

    if vehicle.locked_by != user:
        raise HTTPException(status_code=403, detail="Вы не владелец блокировки")

    vehicle.locked_by = None
    vehicle.locked_at = datetime.utcnow()
    db.commit()
    return {"status": "unlocked"}


# Обновление по ID
@router.put("/{vehicle_id}")
def update_vehicle(vehicle_id: int, data: VehicleUpdate, db: Session = Depends(get_db)):
    check_role(db, data.user, ["admin", "inspector"])

    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="ТС не найдено")

    if vehicle.locked_by and vehicle.locked_by != data.user:
        raise HTTPException(
            status_code=409, detail="ТС редактируется другим пользователем"
        )

    if vehicle.version != data.version:
        raise HTTPException(
            status_code=409, detail="ТС было изменено другим пользователем"
        )

    model = (
        db.query(Model)
        .join(Brand)
        .filter(Model.name == data.model_name, Brand.name == data.brand_name)
        .first()
    )
    color = db.query(Color).filter_by(name=data.color_name).first()
    owner = (
        db.query(Owner)
        .filter_by(last_name=data.owner_last_name, first_name=data.owner_first_name)
        .first()
    )

    if not all([model, color, owner]):
        raise HTTPException(status_code=400, detail="Некорректные данные")

    vehicle.model_id = model.id
    vehicle.color_id = color.id
    vehicle.owner_id = owner.id
    vehicle.version += 1
    vehicle.locked_by = None

    db.commit()
    return {"status": "updated", "new_version": vehicle.version}


# Удаление по ID
@router.delete("/{vehicle_id}")
def delete_vehicle(vehicle_id: int, user: str, db: Session = Depends(get_db)):
    check_role(db, user, ["admin"])

    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="ТС не найдено")
    
    protocol_count = db.query(Protocol).filter(Protocol.vehicle_id == vehicle_id).count()
    if protocol_count > 0:
        raise HTTPException(
            status_code=400,
            detail="Нельзя удалить ТС: существуют связанные протоколы"
        )

    if vehicle.locked_by and vehicle.locked_by != user:
        raise HTTPException(
            status_code=409, detail="ТС редактируется другим пользователем"
        )

    db.delete(vehicle)
    db.commit()
    return {"status": "deleted"}
