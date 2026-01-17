from fastapi import APIRouter, HTTPException
from backend.database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends
from backend.models import Inspector, UserAccount
from backend.schemas import InspectorBase, InspectorOut, InspectorUpdate
from backend.security import check_role
from datetime import datetime
from backend.utils import get_entity_or_404

router = APIRouter(tags=["inspectors"])


@router.get("", response_model=list[InspectorOut])
def get_inspectors(db: Session = Depends(get_db)):
    return db.query(Inspector).order_by(Inspector.last_name).all()


@router.post("", status_code=201)  # Исправлено: добавил слэш
def add_inspector(data: InspectorBase, db: Session = Depends(get_db)):
    check_role(db, data.user, ["admin"])  # user теперь в data

    exists = (
        db.query(Inspector)
        .filter_by(
            last_name=data.last_name,
            first_name=data.first_name,
            middle_name=data.middle_name,
        )
        .first()
    )
    if exists:
        raise HTTPException(status_code=409, detail="Инспектор уже существует")

    inspector = Inspector(**data.dict(exclude={"user"}))  # Исключаем user из данных
    db.add(inspector)
    db.commit()
    return {"status": "ok"}


@router.put("/{inspector_id}")
def update_inspector(inspector_id: int, data: InspectorUpdate, db: Session = Depends(get_db)):
    check_role(db, data.user, ["admin"])

    inspector = get_entity_or_404(db, Inspector, inspector_id)

    # Проверка блокировки
    if inspector.locked_by and inspector.locked_by != data.user:
        raise HTTPException(
            status_code=409, detail="Инспектор редактируется другим пользователем"
        )

    # Проверка версии
    if inspector.version != data.version:
        raise HTTPException(
            status_code=409, detail="Инспектор был изменён другим пользователем"
        )

    # Обновляем поля
    for field, value in data.dict(exclude={"user", "version"}).items():
        setattr(inspector, field, value)

    inspector.version += 1
    inspector.locked_by = None # Разблокируем после успешного обновления
    inspector.locked_at = None 

    db.commit()
    return {"status": "updated", "new_version": inspector.version}


@router.get("/{inspector_id}", response_model=InspectorOut)
def get_inspector(inspector_id: int, db: Session = Depends(get_db)):
    inspector = db.query(Inspector).filter(Inspector.id == inspector_id).first()
    if not inspector:
        raise HTTPException(status_code=404, detail="Инспектор не найден")
    return inspector


@router.post("/lock/{inspector_id}")
def lock_inspector(inspector_id: int, user: str, db: Session = Depends(get_db)):
    inspector = get_entity_or_404(db, Inspector, inspector_id)
    
    if not inspector:
        raise HTTPException(status_code=404, detail="Инспектор не найден")

    if inspector.locked_by and inspector.locked_by != user:
        raise HTTPException(
            status_code=409, detail="Инспектор уже редактируется другим пользователем"
        )

    inspector.locked_by = user
    inspector.locked_at = datetime.utcnow()
    db.commit()
    return {"status": "locked"}


@router.post("/unlock/{inspector_id}")
def unlock_inspector(inspector_id: int, user: str, db: Session = Depends(get_db)):
    inspector = get_entity_or_404(db, Inspector, inspector_id)

    if inspector.locked_by != user:
        raise HTTPException(status_code=403, detail="Вы не владелец блокировки")

    inspector.locked_by = None
    inspector.locked_at = None
    db.commit()
    return {"status": "unlocked"}
