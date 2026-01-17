from database import engine, db_session
from models import (
    Base,
    Brand,
    Model,
    Color,
    Article,
    ViolationType,
    Violation,
    Owner,
    Inspector,
    Vehicle,
    Protocol,
    UserAccount,
)
from datetime import date, time


def init_tables():
    print("Создание таблиц...")
    Base.metadata.create_all(bind=engine)
    print("Таблицы созданы")


def init_reference_data():
    print("Заполнение справочников...")

    # Бренды и модели
    brands = {
        "Toyota": ["Camry", "Corolla"],
        "Ford": ["Focus", "Mondeo"],
        "Kia": ["Rio", "Ceed"],
    }
    brand_objs = {}
    for brand_name, models in brands.items():
        brand = Brand(name=brand_name)
        db_session.add(brand)
        db_session.commit()
        brand_objs[brand_name] = brand
        for model_name in models:
            db_session.add(Model(name=model_name, brand_id=brand.id))

    # Цвета
    colors = ["Белый", "Чёрный", "Серый", "Синий"]
    db_session.add_all([Color(name=c) for c in colors])

    # Статьи
    articles = {
        "12.1": "Превышение скорости",
        "12.2": "Проезд на красный",
        "12.3": "Нарушение правил парковки",
    }
    article_objs = {}
    for num, name in articles.items():
        article = Article(number=num, name=name)
        db_session.add(article)
        db_session.commit()
        article_objs[num] = article

    # Типы нарушений
    types = ["Движение", "Светофор", "Стоянка"]
    type_objs = {}
    for t in types:
        vt = ViolationType(name=t)
        db_session.add(vt)
        db_session.commit()
        type_objs[t] = vt

    # Нарушения
    violations = [
        {"name": "Скорость > 60", "type": "Движение", "article": "12.1"},
        {"name": "Красный свет", "type": "Светофор", "article": "12.2"},
        {"name": "Стоянка на тротуаре", "type": "Стоянка", "article": "12.3"},
    ]
    for v in violations:
        db_session.add(
            Violation(
                name=v["name"],
                violation_type_id=type_objs[v["type"]].id,
                article_id=article_objs[v["article"]].id,
            )
        )

    db_session.commit()
    print("Справочники заполнены")


def init_main_data():
    print("Добавление владельцев, инспекторов, ТС и протоколов...")

    # Владельцы
    owners = [
        Owner(
            last_name="Иванов",
            first_name="Пётр",
            middle_name="Сергеевич",
            date_of_birth=date(1985, 5, 12),
            address="ул. Ленина, 10",
        ),
        Owner(
            last_name="Сидоров",
            first_name="Алексей",
            middle_name="Игоревич",
            date_of_birth=date(1990, 8, 22),
            address="пр. Мира, 25",
        ),
    ]
    db_session.add_all(owners)
    db_session.commit()

    # Инспекторы
    inspectors = [
        Inspector(
            last_name="Кузнецов",
            first_name="Илья",
            middle_name="Викторович",
            department="ГИБДД Центральный",
            rank="капитан",
        ),
        Inspector(
            last_name="Морозов",
            first_name="Андрей",
            middle_name="Павлович",
            department="ГИБДД Восточный",
            rank="лейтенант",
        ),
    ]
    db_session.add_all(inspectors)
    db_session.commit()

    # ТС
    model_camry = db_session.query(Model).filter_by(name="Camry").first()
    model_focus = db_session.query(Model).filter_by(name="Focus").first()
    color_white = db_session.query(Color).filter_by(name="Белый").first()
    color_black = db_session.query(Color).filter_by(name="Чёрный").first()

    vehicles = [
        Vehicle(
            state_number="A123BC",
            model_id=model_camry.id,
            color_id=color_white.id,
            owner_id=owners[0].id,
        ),
        Vehicle(
            state_number="B456DE",
            model_id=model_focus.id,
            color_id=color_black.id,
            owner_id=owners[1].id,
        ),
    ]
    db_session.add_all(vehicles)
    db_session.commit()

    # Протоколы
    violation_speed = (
        db_session.query(Violation).filter_by(name="Скорость > 60").first()
    )
    violation_stop = (
        db_session.query(Violation).filter_by(name="Стоянка на тротуаре").first()
    )

    protocols = [
        Protocol(
            number="PR-001",
            issue_date=date(2025, 9, 18),
            issue_time=time(12, 0),
            vehicle_id=vehicles[0].id,
            owner_id=owners[0].id,
            inspector_id=inspectors[0].id,
            violation_id=violation_speed.id,
        ),
        Protocol(
            number="PR-002",
            issue_date=date(2025, 9, 17),
            issue_time=time(15, 30),
            vehicle_id=vehicles[1].id,
            owner_id=owners[1].id,
            inspector_id=inspectors[1].id,
            violation_id=violation_stop.id,
        ),
    ]
    db_session.add_all(protocols)
    db_session.commit()

    # Пользователи
    existing_admin = db_session.query(UserAccount).filter_by(username="admin").first()
    existing_admin1 = db_session.query(UserAccount).filter_by(username="admin1").first()
    existing_inspector = (
        db_session.query(UserAccount).filter_by(username="inspector1").first()
    )
    existing_inspector2 = (
        db_session.query(UserAccount).filter_by(username="inspector2").first()
    )

    if not existing_admin:
        db_session.add(UserAccount(username="admin", role="admin"))
    if not existing_admin1:
        db_session.add(UserAccount(username="admin1", role="admin"))
    if not existing_inspector:
        db_session.add(UserAccount(username="inspector1", role="inspector"))
    if not existing_inspector2:
        db_session.add(UserAccount(username="inspector2", role="inspector"))

    db_session.commit()

    print("Основные данные добавлены")


if __name__ == "__main__":
    init_tables()
    try:
        init_reference_data()
        init_main_data()
    except Exception as e:
        print("Ошибка при инициализации:", e)
