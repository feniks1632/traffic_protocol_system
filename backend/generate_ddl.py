# generate_schema.py
from sqlalchemy import create_engine
from sqlalchemy.schema import CreateTable
from models import Base

engine = create_engine("postgresql://postgres:1234@localhost:5432/violation_db")

with open("schema.sql", "w", encoding="utf-8") as f:
    f.write("-- Физическая модель БД: сгенерировано из SQLAlchemy-моделей\n\n")
    for table in Base.metadata.sorted_tables:
        f.write(str(CreateTable(table).compile(engine)))
        f.write("\n")