# backend/utils.py
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session

LOCK_TIMEOUT_SECONDS = 45  # можно менять


def clear_expired_lock(entity):
    if entity.locked_by and entity.locked_at:
        now = datetime.utcnow()
        if now - entity.locked_at > timedelta(seconds=LOCK_TIMEOUT_SECONDS):
            entity.locked_by = None
            entity.locked_at = None


def get_entity_or_404(db: Session, model, entity_id: int):
    entity = db.get(model, entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail=f"{model.__name__} не найден")
    clear_expired_lock(entity)
    return entity