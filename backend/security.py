# backend/security.py
from fastapi import HTTPException
from backend.models import UserAccount

def check_role(db, username: str, allowed_roles: list):
    """
    Проверяет роль пользователя.
    db — сессия SQLAlchemy (Session).
    """
    user = db.query(UserAccount).filter_by(username=username).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if user.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="Недостаточно прав")