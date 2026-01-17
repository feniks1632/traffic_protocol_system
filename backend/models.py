from sqlalchemy import Column, Integer, String, Date, Time, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class UserAccount(Base):
    __tablename__ = "user_account"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    role = Column(String(20), nullable=False)  # 'admin' or 'inspector'


class Owner(Base):
    __tablename__ = "owner"
    id = Column(Integer, primary_key=True)
    last_name = Column(String(50), nullable=False)
    first_name = Column(String(50), nullable=False)
    middle_name = Column(String(50), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    address = Column(String(100), nullable=False)
    version = Column(Integer, default=1, nullable=False)
    vehicles = relationship("Vehicle", back_populates="owner", cascade="all, delete")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    locked_by = Column(String, nullable=True)
    locked_at = Column(DateTime, nullable=True)


class Inspector(Base):
    __tablename__ = "inspector"
    id = Column(Integer, primary_key=True)
    last_name = Column(String(50), nullable=False)
    first_name = Column(String(50), nullable=False)
    middle_name = Column(String(50), nullable=False)
    department = Column(String(100), nullable=False)
    rank = Column(String(50), nullable=False)
    version = Column(Integer, default=1, nullable=False)
    protocols = relationship("Protocol", back_populates="inspector")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    locked_by = Column(String, nullable=True)
    locked_at = Column(DateTime, nullable=True)


class Brand(Base):
    __tablename__ = "brand"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    version = Column(Integer, default=1, nullable=False)


class Model(Base):
    __tablename__ = "model"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    brand_id = Column(Integer, ForeignKey("brand.id"), nullable=False)
    version = Column(Integer, default=1, nullable=False)
    brand = relationship("Brand")
    vehicles = relationship("Vehicle", back_populates="model", cascade="all, delete")
    locked_by = Column(String, nullable=True)
    locked_at = Column(DateTime, nullable=True)


class Color(Base):
    __tablename__ = "color"
    id = Column(Integer, primary_key=True)
    name = Column(String(30), unique=True, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    locked_by = Column(String, nullable=True)
    locked_at = Column(DateTime, nullable=True)


class Vehicle(Base):
    __tablename__ = "vehicle"
    id = Column(Integer, primary_key=True)
    state_number = Column(String(20), unique=True, nullable=False)
    model_id = Column(Integer, ForeignKey("model.id"), nullable=False)
    color_id = Column(Integer, ForeignKey("color.id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("owner.id"), nullable=False)
    version = Column(Integer, default=1, nullable=False)
    model = relationship("Model", back_populates="vehicles")
    color = relationship("Color")
    owner = relationship("Owner", back_populates="vehicles")
    protocols = relationship("Protocol", back_populates="vehicle")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    locked_by = Column(String, nullable=True)
    locked_at = Column(DateTime, nullable=True)


class ViolationType(Base):
    __tablename__ = "violation_type"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    locked_by = Column(String, nullable=True)
    locked_at = Column(DateTime, nullable=True)


class Article(Base):
    __tablename__ = "article"
    id = Column(Integer, primary_key=True)
    number = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)
    version = Column(Integer, default=1, nullable=False)
    locked_by = Column(String, nullable=True)
    locked_at = Column(DateTime, nullable=True)


class Violation(Base):
    __tablename__ = "violation"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    violation_type_id = Column(Integer, ForeignKey("violation_type.id"), nullable=False)
    article_id = Column(Integer, ForeignKey("article.id"), nullable=False)
    version = Column(Integer, default=1, nullable=False)
    violation_type = relationship("ViolationType")
    article = relationship("Article")
    protocols = relationship("Protocol", back_populates="violation")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    locked_by = Column(String, nullable=True)
    locked_at = Column(DateTime, nullable=True)


class Protocol(Base):
    __tablename__ = "protocol"
    id = Column(Integer, primary_key=True)
    number = Column(String(20), unique=True, nullable=False)
    issue_date = Column(Date, nullable=False)
    issue_time = Column(Time, nullable=False)
    vehicle_id = Column(Integer, ForeignKey("vehicle.id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("owner.id"), nullable=False)
    inspector_id = Column(Integer, ForeignKey("inspector.id"), nullable=False)
    violation_id = Column(Integer, ForeignKey("violation.id"), nullable=False)
    version = Column(Integer, default=1, nullable=False)
    vehicle = relationship("Vehicle", back_populates="protocols")
    owner = relationship("Owner")
    inspector = relationship("Inspector", back_populates="protocols")
    violation = relationship("Violation", back_populates="protocols")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    locked_by = Column(String, nullable=True)
    locked_at = Column(DateTime, nullable=True)
