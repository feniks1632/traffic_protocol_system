from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session 
from backend.database import get_db
from backend.models import UserAccount
from backend.schemas import UserLogin, UserInfo

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=UserInfo)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(UserAccount).filter_by(username=data.username).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return {"username": user.username, "role": user.role}