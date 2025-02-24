from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import enum


class StarshipStatus(str, enum.Enum):
    AVAILABLE = "available"
    MAINTENANCE = "maintenance"
    IN_FLIGHT = "in_flight"
    LOADING = "loading"


class StarshipBase(BaseModel):
    name: str = Field(
        ..., 
        min_length=2, 
        max_length=100,
        description="Название звездолета (от 2 до 100 символов)"
    )
    capacity: float = Field(
        ..., 
        gt=0,
        le=1000000,
        description="Грузоподъемность в тоннах (от 0 до 1,000,000)"
    )
    volume: float = Field(
        ..., 
        gt=0,
        le=1000000,
        description="Объем грузового отсека в кубометрах (от 0 до 1,000,000)"
    )
    range: float = Field(
        ..., 
        gt=0,
        le=10000000,
        description="Дальность полета в световых годах (от 0 до 10,000,000)"
    )
    status: StarshipStatus = Field(default=StarshipStatus.AVAILABLE, description="Статус звездолета")

    @validator('capacity')
    def validate_capacity(cls, v):
        if v > 1000000:  # максимум 1000 тонн
            raise ValueError('Грузоподъемность не может превышать 1000 тонн')
        return v

    @validator('range')
    def validate_range(cls, v):
        if v > 100000000:  # максимум 100 млн км
            raise ValueError('Дальность не может превышать 100 млн километров')
        return v


class StarshipCreate(StarshipBase):
    pass


class StarshipUpdate(StarshipBase):
    name: Optional[str] = None
    capacity: Optional[float] = None
    range: Optional[float] = None
    status: Optional[StarshipStatus] = None


class Starship(StarshipBase):
    id: int

    class Config:
        from_attributes = True


class CargoBase(BaseModel):
    name: str = Field(
        ..., 
        min_length=2, 
        max_length=100,
        description="Название груза (от 2 до 100 символов)"
    )
    quantity: int = Field(
        ..., 
        ge=0,
        le=1000000,
        description="Количество единиц груза (от 0 до 1,000,000)"
    )
    weight: float = Field(
        ..., 
        gt=0,
        le=1000,
        description="Вес одной единицы в тоннах (от 0 до 1,000)"
    )
    volume: float = Field(
        ..., 
        gt=0,
        le=1000,
        description="Объем одной единицы в кубических метрах (от 0 до 1,000)"
    )

    @validator('weight', 'volume')
    def validate_positive(cls, v):
        if v <= 0:
            raise ValueError("Значение должно быть положительным")
        return v


class CargoCreate(CargoBase):
    pass


class CargoUpdate(CargoBase):
    name: Optional[str] = None
    quantity: Optional[int] = None
    weight: Optional[float] = None
    volume: Optional[float] = None


class Cargo(CargoBase):
    id: int

    class Config:
        from_attributes = True


class ShipmentStatus(str, enum.Enum):
    LOADING = "loading"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ShipmentCreate(BaseModel):
    starship_id: int = Field(..., description="ID звездолета")
    cargo_id: int = Field(..., description="ID груза")
    quantity: int = Field(
        ..., 
        gt=0,
        description="Количество единиц груза для погрузки (больше 0)"
    )


class ShipmentResponse(BaseModel):
    id: int
    starship_id: int
    starship_name: str
    cargo_id: int
    cargo_name: str
    quantity: int
    status: ShipmentStatus
    created_at: datetime

    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    detail: str
