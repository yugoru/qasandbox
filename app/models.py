from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()


class StarshipStatus(str, enum.Enum):
    AVAILABLE = "available"
    MAINTENANCE = "maintenance"
    IN_FLIGHT = "in_flight"
    LOADING = "loading"


class Starship(Base):
    __tablename__ = "starships"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    capacity = Column(Float, nullable=False)  # в килограммах
    volume = Column(Float, nullable=False)  # объем единицы в м³
    range = Column(Float, nullable=False)  # в километрах
    status = Column(Enum(StarshipStatus, name="starshipstatus", create_type=False), default=StarshipStatus.AVAILABLE, nullable=False)

    # Добавляем ограничения
    __table_args__ = (
        CheckConstraint('capacity > 0', name='check_positive_capacity'),
        CheckConstraint('range > 0', name='check_positive_range'),
        CheckConstraint('length(name) >= 2', name='check_name_length'),
    )


class Cargo(Base):
    __tablename__ = "cargo"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True, nullable=False)
    quantity = Column(Integer, nullable=False)
    weight = Column(Float, nullable=False)  # вес единицы в кг
    volume = Column(Float, nullable=False)  # объем единицы в м³

    # Добавляем ограничения
    __table_args__ = (
        CheckConstraint('quantity >= 0', name='check_non_negative_quantity'),
        CheckConstraint('weight > 0', name='check_positive_weight'),
        CheckConstraint('volume > 0', name='check_positive_volume'),
        CheckConstraint('weight <= 10000', name='check_max_weight'),  # максимум 10 тонн на единицу
        CheckConstraint('volume <= 1000', name='check_max_volume'),  # максимум 1000 м³
    )


class ShipmentStatus(str, enum.Enum):
    LOADING = "loading"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class ShipmentHistory(Base):
    __tablename__ = "shipment_history"

    id = Column(Integer, primary_key=True, index=True)
    starship_id = Column(Integer, ForeignKey("starships.id"))
    cargo_id = Column(Integer, ForeignKey("cargo.id"))
    quantity = Column(Integer)
    status = Column(Enum(ShipmentStatus, name="shipmentstatus", create_type=False))
    created_at = Column(DateTime, default=datetime.utcnow)
