from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Violation, ViolationType, Article, UserAccount
from backend.schemas import (
    ViolationBase,
    ViolationOut,
    ViolationTypeOut,
    ArticleOut,
    ViolationUpdate,
)
from backend.security import check_role

router = APIRouter(tags=["violations"])


@router.get("", response_model=list[ViolationOut])
def get_violations(type: str = Query(None), db: Session = Depends(get_db)):
    query = db.query(Violation).join(ViolationType).join(Article)
    if type:
        query = query.filter(ViolationType.name == type)
    violations = query.all()
    return [
        {
            "id": v.id,
            "name": v.name,
            "type": v.violation_type.name,
            "article_number": v.article.number,
            "article_name": v.article.name,
            "version": v.version,
        }
        for v in violations
    ]


@router.post("", status_code=201)
def add_violation(data: ViolationBase, db: Session = Depends(get_db)):
    check_role(db, data.user, ["admin", "inspector"])

    vt = db.query(ViolationType).filter_by(name=data.type).first()
    if not vt:
        vt = ViolationType(name=data.type)
        db.add(vt)
        db.commit()

    article = db.query(Article).filter_by(number=data.article_number).first()
    if not article:
        article = Article(number=data.article_number, name=data.article_name)
        db.add(article)
        db.commit()

    exists = db.query(Violation).filter_by(name=data.name).first()
    if exists:
        raise HTTPException(status_code=409, detail="Нарушение уже существует")

    violation = Violation(
        name=data.name, violation_type_id=vt.id, article_id=article.id
    )
    db.add(violation)
    db.commit()
    return {"status": "ok"}


@router.put("/{violation_id}")
def update_violation(violation_id: int, data: ViolationUpdate, db: Session = Depends(get_db)):
    check_role(db, data.user, ["admin", "inspector"])

    violation = db.query(Violation).filter(Violation.id == violation_id).first()
    if not violation:
        raise HTTPException(status_code=404, detail="Нарушение не найдено")

    # Проверка блокировки
    if violation.locked_by and violation.locked_by != data.user:
        raise HTTPException(
            status_code=409, detail="Нарушение редактируется другим пользователем"
        )

    # Проверка версии
    if violation.version != data.version:
        raise HTTPException(
            status_code=409, detail="Нарушение было изменено другим пользователем"
        )

    vt = db.query(ViolationType).filter_by(name=data.type).first()
    if not vt:
        vt = ViolationType(name=data.type)
        db.add(vt)
        db.commit()

    article = db.query(Article).filter_by(number=data.article_number).first()
    if not article:
        article = Article(number=data.article_number, name=data.article_name)
        db.add(article)
        db.commit()

    violation.name = data.name
    violation.violation_type_id = vt.id
    violation.article_id = article.id
    violation.version += 1
    violation.locked_by = None  # Разблокируем после обновления

    db.commit()
    return {"status": "updated", "new_version": violation.version}


@router.get("/violation-types", response_model=list[ViolationTypeOut])
def get_violation_types(db: Session = Depends(get_db)):
    return db.query(ViolationType).order_by(ViolationType.name).all()


@router.get("/articles", response_model=list[ArticleOut])
def get_articles(db: Session = Depends(get_db)):
    return db.query(Article).order_by(Article.number).all()


# Получить одно нарушение по ID
@router.get("/{violation_id}", response_model=ViolationOut)
def get_violation(violation_id: int, db: Session = Depends(get_db)):
    violation = db.query(Violation).filter(Violation.id == violation_id).first()
    if not violation:
        raise HTTPException(status_code=404, detail="Нарушение не найдено")

    return {
        "id": violation.id,
        "name": violation.name,
        "type": violation.violation_type.name,
        "article_number": violation.article.number,
        "article_name": violation.article.name,
        "version": violation.version,
    }


# Блокировка нарушения
@router.post("/lock/{violation_id}")
def lock_violation(violation_id: int, user: str, db: Session = Depends(get_db)):
    violation = db.query(Violation).filter(Violation.id == violation_id).first()
    if not violation:
        raise HTTPException(status_code=404, detail="Нарушение не найдено")

    if violation.locked_by and violation.locked_by != user:
        raise HTTPException(
            status_code=409, detail="Нарушение уже редактируется другим пользователем"
        )

    violation.locked_by = user
    violation.locked_at = datetime.utcow()
    db.commit()
    return {"status": "locked"}


# Разблокировка нарушения
@router.post("/unlock/{violation_id}")
def unlock_violation(violation_id: int, user: str, db: Session = Depends(get_db)):
    violation = db.query(Violation).filter(Violation.id == violation_id).first()
    if not violation:
        raise HTTPException(status_code=404, detail="Нарушение не найдено")

    if violation.locked_by != user:
        raise HTTPException(status_code=403, detail="Вы не владелец блокировки")

    violation.locked_by = None
    db.commit()
    return {"status": "unlocked"}
