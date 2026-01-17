from typing import Optional
from pydantic import BaseModel
from datetime import date, time


# 🔐 Авторизация
class UserLogin(BaseModel):
    username: str


class UserInfo(BaseModel):
    username: str
    role: str


# 👤 Владельцы
class OwnerBase(BaseModel):
    last_name: str
    first_name: str
    middle_name: str
    date_of_birth: date
    address: str
    user: str


class OwnerOut(BaseModel):
    id: int
    last_name: str
    first_name: str
    middle_name: str
    date_of_birth: date
    address: str
    version: int
    locked_by: Optional[str] = None

    class Config:
        orm_mode = True


class OwnerUpdate(BaseModel):
    last_name: str
    first_name: str
    middle_name: str
    date_of_birth: str
    address: str
    user: str
    version: int


# 👮 Инспекторы
class InspectorBase(BaseModel):
    last_name: str
    first_name: str
    middle_name: str
    department: str
    rank: str
    user: str


class InspectorOut(BaseModel):
    id: int
    last_name: str
    first_name: str
    middle_name: str
    department: str
    rank: str
    version: int
    locked_by: Optional[str] = None

    class Config:
        orm_mode = True


class InspectorUpdate(BaseModel):
    last_name: str
    first_name: str
    middle_name: str
    department: str
    rank: str
    user: str
    version: int


# 🚘 Транспорт
class VehicleBase(BaseModel):
    state_number: str
    model_name: str
    brand_name: str
    color_name: str
    owner_last_name: str
    owner_first_name: str
    user: str


class VehicleOut(BaseModel):
    id: int
    state_number: str
    locked_by: Optional[str] = None
    model: str
    color: str
    owner: str
    version: int

    class Config:
        orm_mode = True


class VehicleUpdate(BaseModel):
    model_name: str
    brand_name: str
    color_name: str
    owner_last_name: str
    owner_first_name: str
    user: str
    version: int


# ⚠️ Нарушения
class ViolationBase(BaseModel):
    name: str
    type: str
    article_number: str
    article_name: str
    user: str


class ViolationOut(BaseModel):
    id: int
    name: str
    type: str
    article_number: str
    article_name: str
    version: int
    locked_by: Optional[str] = None

    class Config:
        orm_mode = True


class ViolationUpdate(BaseModel):
    name: str
    type: str
    article_number: str
    article_name: str
    user: str
    version: int


# 📚 Справочники
class ViolationTypeOut(BaseModel):
    id: int
    name: str


class ArticleOut(BaseModel):
    id: int
    number: str
    name: str


class ModelOut(BaseModel):
    id: int
    name: str
    brand: str


class ColorOut(BaseModel):
    id: int
    name: str


# 📄 Протоколы
class ProtocolBase(BaseModel):
    number: str
    issue_date: date
    issue_time: time
    vehicle: str
    owner: str
    inspector: str
    violation: str
    user: str


class ProtocolOut(BaseModel):
    id: int
    number: str
    issue_date: date
    issue_time: time
    vehicle: str
    owner: str
    inspector: str
    violation: str
    version: int
    locked_by: Optional[str] = None

    class Config:
        orm_mode = True


class ProtocolUpdate(BaseModel):
    issue_date: str
    issue_time: str
    vehicle: str
    owner: str
    inspector: str
    violation: str
    user: str
    version: int
