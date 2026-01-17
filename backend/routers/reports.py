from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Inspector, Owner, Vehicle, Protocol, Violation

router = APIRouter(tags=["reports"])


@router.get("/inspectors")
def report_inspectors(db: Session = Depends(get_db)):
    """Отчёт: все инспекторы"""
    inspectors = db.query(Inspector).all()
    return [
        {
            "id": i.id,
            "ФИО": f"{i.last_name} {i.first_name} {i.middle_name}",
            "Отдел": i.department,
            "Звание": i.rank,
            "Создано": i.created_at.isoformat() if i.created_at else None,
        }
        for i in inspectors
    ]


@router.get("/owners")
def report_owners(db: Session = Depends(get_db)):
    """Отчёт: владельцы + их ТС + нарушения"""
    owners = db.query(Owner).all()
    result = []
    for owner in owners:
        vehicles = []
        for vehicle in owner.vehicles:
            violations = []
            for protocol in vehicle.protocols:
                violations.append({
                    "Нарушение": protocol.violation.name,
                    "Статья": f"{protocol.violation.article.number} — {protocol.violation.article.name}",
                    "Дата": protocol.issue_date.isoformat(),
                    "Инспектор": f"{protocol.inspector.last_name} {protocol.inspector.first_name}",
                })
            vehicles.append({
                "Гос. номер": vehicle.state_number,
                "Модель": f"{vehicle.model.name} ({vehicle.model.brand.name})",
                "Цвет": vehicle.color.name,
                "Нарушения": violations,
            })
        result.append({
            "Владелец": f"{owner.last_name} {owner.first_name} {owner.middle_name}",
            "Дата рождения": owner.date_of_birth.isoformat(),
            "Адрес": owner.address,
            "ТС": vehicles,
        })
    return result


@router.get("/violations")
def report_violations(db: Session = Depends(get_db)):
    """Отчёт: все нарушения"""
    violations = db.query(Violation).all()
    return [
        {
            "id": v.id,
            "Нарушение": v.name,
            "Тип": v.violation_type.name,
            "Статья": f"{v.article.number} — {v.article.name}",
            "Создано": v.created_at.isoformat() if v.created_at else None,
        }
        for v in violations
    ]