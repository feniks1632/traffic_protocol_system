from datetime import datetime
from fastapi import APIRouter, HTTPException
from backend.database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends
from backend.models import Owner, UserAccount
from backend.schemas import OwnerBase, OwnerOut, OwnerUpdate
from backend.security import check_role

router = APIRouter(tags=["owners"])


@router.get("", response_model=list[OwnerOut])
def get_owners(db: Session = Depends(get_db)):
    return db.query(Owner).order_by(Owner.last_name).all()


@router.post("", status_code=201)
def add_owner(data: OwnerBase, db: Session = Depends(get_db)):
    check_role(db, data.user, ["admin", "inspector"])

    exists = (
        db.query(Owner)
        .filter_by(
            last_name=data.last_name,
            first_name=data.first_name,
            middle_name=data.middle_name,
        )
        .first()
    )
    if exists:
        raise HTTPException(status_code=409, detail="Владелец уже существует")

    owner = Owner(**data.dict(exclude={"user"}))
    db.add(owner)
    db.commit()
    return {"status": "ok"}


@router.put("/{owner_id}")
def update_owner(owner_id: int, data: OwnerUpdate, db: Session = Depends(get_db)):
    check_role(db, data.user, ["admin", "inspector"])

    owner = db.query(Owner).filter(Owner.id == owner_id).first()
    if not owner:
        print("[ERROR] Owner not found in DB!")
        all_ids = [o.id for o in db.query(Owner).all()]
        print(f"[DEBUG] Existing IDs: {all_ids}")
        raise HTTPException(status_code=404, detail="Владелец не найден")

    if not owner:
        raise HTTPException(status_code=404, detail="Владелец не найден")

    if owner.locked_by and owner.locked_by != data.user:
        raise HTTPException(
            status_code=409, detail="Владелец редактируется другим пользователем"
        )

    if owner.version != data.version:
        raise HTTPException(
            status_code=409, detail="Владелец был изменён другим пользователем"
        )

    for field, value in data.dict(exclude={"user", "version"}).items():
        setattr(owner, field, value)
    owner.version += 1

    db.commit()
    return {"status": "updated", "new_version": owner.version}


@router.post("/lock/{owner_id}")
def lock_owner(owner_id: int, user: str, db: Session = Depends(get_db)):
    owner = db.query(Owner).filter(Owner.id == owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Владелец не найден")

    if owner.locked_by and owner.locked_by != user:
        raise HTTPException(
            status_code=409, detail="Владелец уже редактируется другим пользователем"
        )

    owner.locked_by = user
    owner.locked_at = datetime.utcnow() 
    db.commit()
    return {"status": "locked"}


@router.post("/unlock/{owner_id}")
def unlock_owner(owner_id: int, user: str, db: Session = Depends(get_db)):
    owner = db.query(Owner).filter(Owner.id == owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Владелец не найден")
    if owner.locked_by != user:
        raise HTTPException(status_code=403, detail="Вы не владелец блокировки")
    owner.locked_by = None
    owner.locked_at = None
    db.commit()
    return {"status": "unlocked"}


@router.get("/{owner_id}", response_model=OwnerOut)
def get_owner(owner_id: int, db: Session = Depends(get_db)):
    owner = db.query(Owner).filter(Owner.id == owner_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Владелец не найден")
    return owner