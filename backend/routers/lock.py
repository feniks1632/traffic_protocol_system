from fastapi import APIRouter, Depends, HTTPException
from backend.database import get_db
from sqlalchemy.orm import Session 
from backend.database import get_db
from datetime import datetime, timedelta
from backend.models import (
    Vehicle,
    Owner,
    Inspector,
    Protocol,
    Violation,
    Model,
    Color,
    Article,
    ViolationType,
)

router = APIRouter(tags=["locks"])

MODEL_MAP = {
    "vehicle": Vehicle,
    "owner": Owner,
    "inspector": Inspector,
    "protocol": Protocol,
    "violation": Violation,
    "model": Model,
    "color": Color,
    "article": Article,
    "violation_type": ViolationType,
}


@router.post("/lock/{entity}/{id}")
def lock_entity(entity: str, id: int, user: str, db: Session = Depends(get_db)):
    model = MODEL_MAP.get(entity)
    if not model:
        raise HTTPException(status_code=400, detail="Неизвестный тип сущности")

    obj = db.query(model).get(id)
    if not obj:
        raise HTTPException(status_code=404, detail="Объект не найден")

    # Авторазблокировка по таймауту
    if obj.locked_at and datetime.utcnow() - obj.locked_at > timedelta(minutes=1):
        obj.locked_by = None
        obj.locked_at = None

    if obj.locked_by and obj.locked_by != user:
        raise HTTPException(
            status_code=409, detail="Объект редактируется другим пользователем"
        )

    obj.locked_by = user
    obj.locked_at = datetime.utcnow()
    db.commit()
    return {"status": "locked"}


@router.post("/unlock/{entity}/{id}")
def unlock_entity(entity: str, id: int, user: str, db: Session = Depends(get_db)):
    model = MODEL_MAP.get(entity)
    if not model:
        raise HTTPException(status_code=400, detail="Неизвестный тип сущности")

    obj = db.query(model).get(id)
    if not obj:
        raise HTTPException(status_code=404, detail="Объект не найден")

    if obj.locked_by != user:
        raise HTTPException(status_code=403, detail="Вы не владелец блокировки")

    obj.locked_by = None
    obj.locked_at = None
    db.commit()
    return {"status": "unlocked"}
