from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Protocol, Vehicle, Owner, Inspector, Violation, UserAccount
from backend.schemas import ProtocolBase, ProtocolOut, ProtocolUpdate
from backend.security import check_role

router = APIRouter(tags=["protocols"])


@router.get("", response_model=list[ProtocolOut])
def get_protocols(db: Session = Depends(get_db)):
    protocols = db.query(Protocol).all()
    result = []
    for p in protocols:
        result.append(
            {
                "id": p.id,
                "number": p.number,
                "issue_date": p.issue_date,
                "issue_time": p.issue_time,
                "vehicle": p.vehicle.state_number,
                "owner": f"{p.owner.last_name} {p.owner.first_name}",
                "inspector": f"{p.inspector.last_name} {p.inspector.first_name}",
                "violation": p.violation.name,
                "version": p.version,
            }
        )
    return result


@router.post("", status_code=201)
def add_protocol(data: ProtocolBase, db: Session = Depends(get_db)):
    check_role(db, data.user, ["admin", "inspector"])

    exists = db.query(Protocol).filter_by(number=data.number).first()
    if exists:
        raise HTTPException(status_code=409, detail="Протокол уже существует")

    vehicle = db.query(Vehicle).filter_by(state_number=data.vehicle).first()
    owner_last, owner_first = data.owner.split(" ")
    owner = (
        db.query(Owner)
        .filter_by(last_name=owner_last, first_name=owner_first)
        .first()
    )
    inspector_last, inspector_first = data.inspector.split(" ")
    inspector = (
        db.query(Inspector)
        .filter_by(last_name=inspector_last, first_name=inspector_first)
        .first()
    )
    violation = db.query(Violation).filter_by(name=data.violation).first()

    if not all([vehicle, owner, inspector, violation]):
        raise HTTPException(status_code=400, detail="Некорректные данные")

    protocol = Protocol(
        number=data.number,
        issue_date=data.issue_date,
        issue_time=data.issue_time,
        vehicle_id=vehicle.id,
        owner_id=owner.id,
        inspector_id=inspector.id,
        violation_id=violation.id,
    )
    db.add(protocol)
    db.commit()
    return {"status": "ok"}


@router.put("/{protocol_id}")
def update_protocol(protocol_id: int, data: ProtocolUpdate, db: Session = Depends(get_db)):
    check_role(db, data.user, ["admin", "inspector"])

    protocol = db.query(Protocol).filter(Protocol.id == protocol_id).first()
    if not protocol:
        raise HTTPException(status_code=404, detail="Протокол не найден")

    # Проверка блокировки
    if protocol.locked_by and protocol.locked_by != data.user:
        raise HTTPException(
            status_code=409, detail="Протокол редактируется другим пользователем"
        )

    # Проверка версии
    if protocol.version != data.version:
        raise HTTPException(
            status_code=409, detail="Протокол был изменён другим пользователем"
        )

    vehicle = db.query(Vehicle).filter_by(state_number=data.vehicle).first()
    owner_last, owner_first = data.owner.split(" ")
    owner = (
        db.query(Owner)
        .filter_by(last_name=owner_last, first_name=owner_first)
        .first()
    )
    inspector_last, inspector_first = data.inspector.split(" ")
    inspector = (
        db.query(Inspector)
        .filter_by(last_name=inspector_last, first_name=inspector_first)
        .first()
    )
    violation = db.query(Violation).filter_by(name=data.violation).first()

    if not all([vehicle, owner, inspector, violation]):
        raise HTTPException(status_code=400, detail="Некорректные данные")

    protocol.number = data.number
    protocol.issue_date = data.issue_date
    protocol.issue_time = data.issue_time
    protocol.vehicle_id = vehicle.id
    protocol.owner_id = owner.id
    protocol.inspector_id = inspector.id
    protocol.violation_id = violation.id
    protocol.version += 1
    protocol.locked_by = None  # Разблокируем после обновления

    db.commit()
    return {"status": "updated", "new_version": protocol.version}


# Получить один протокол по ID
@router.get("/{protocol_id}", response_model=ProtocolOut)
def get_protocol(protocol_id: int, db: Session = Depends(get_db)):
    protocol = db.query(Protocol).filter(Protocol.id == protocol_id).first()
    if not protocol:
        raise HTTPException(status_code=404, detail="Протокол не найден")

    return {
        "id": protocol.id,
        "number": protocol.number,
        "issue_date": protocol.issue_date,
        "issue_time": protocol.issue_time,
        "vehicle": protocol.vehicle.state_number,
        "owner": f"{protocol.owner.last_name} {protocol.owner.first_name}",
        "inspector": f"{protocol.inspector.last_name} {protocol.inspector.first_name}",
        "violation": protocol.violation.name,
        "version": protocol.version,
    }


# Блокировка протокола
@router.post("/lock/{protocol_id}")
def lock_protocol(protocol_id: int, user: str, db: Session = Depends(get_db)):
    protocol = db.query(Protocol).filter(Protocol.id == protocol_id).first()
    if not protocol:
        raise HTTPException(status_code=404, detail="Протокол не найден")

    if protocol.locked_by and protocol.locked_by != user:
        raise HTTPException(
            status_code=409, detail="Протокол уже редактируется другим пользователем"
        )

    protocol.locked_by = user
    protocol.locked_at = datetime.utcnow
    db.commit()
    return {"status": "locked"}


# Разблокировка протокола
@router.post("/unlock/{protocol_id}")
def unlock_protocol(protocol_id: int, user: str):
    protocol = db_session.query(Protocol).filter(Protocol.id == protocol_id).first()
    if not protocol:
        raise HTTPException(status_code=404, detail="Протокол не найден")

    if protocol.locked_by != user:
        raise HTTPException(status_code=403, detail="Вы не владелец блокировки")

    protocol.locked_by = None
    db_session.commit()
    return {"status": "unlocked"}
