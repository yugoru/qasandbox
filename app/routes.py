from fastapi import APIRouter, Depends, Query, Body, HTTPException, Path, Request
from sqlalchemy.orm import Session
from starlette import status
from datetime import datetime
from typing import List, Optional

from app import schemas, models
from app.db import get_db
from app.limiter import limiter
from config import RATE_LIMIT_PER_MINUTE

router = APIRouter()

@router.get(
    "/api/starships",
    response_model=List[schemas.Starship],
    tags=["starships"],
    summary="Получить список всех звездолетов",
    response_description="Список всех зарегистрированных звездолетов",
    responses={
        200: {
            "description": "Успешное получение списка звездолетов",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "name": "Millennium Falcon",
                            "capacity": 100000,
                            "range": 1000000,
                            "status": "available"
                        }
                    ]
                }
            }
        },
        500: {
            "description": "Внутренняя ошибка сервера",
            "content": {
                "application/json": {
                    "example": {"detail": "Ошибка при получении списка звездолетов"}
                }
            }
        }
    }
)
@limiter.limit(RATE_LIMIT_PER_MINUTE["default"])
async def get_starships(request: Request, db: Session = Depends(get_db)):
    """
    Получает список всех звездолетов в системе.
    """
    return db.query(models.Starship).all()

@router.get(
    "/api/inventory",
    response_model=List[schemas.Cargo],
    tags=["cargo"],
    summary="Получить список всех грузов на складе",
    response_description="Список доступных грузов",
    responses={
        200: {
            "description": "Успешное получение списка грузов",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": 1,
                            "name": "Dilithium Crystals",
                            "quantity": 100,
                            "weight": 10.5,
                            "volume": 2.3
                        }
                    ]
                }
            }
        },
        500: {
            "description": "Внутренняя ошибка сервера",
            "content": {
                "application/json": {
                    "example": {"detail": "Ошибка при получении списка грузов"}
                }
            }
        }
    }
)
@limiter.limit(RATE_LIMIT_PER_MINUTE["default"])
async def get_inventory(
    request: Request,
    skip: int = Query(0, description="Количество пропускаемых записей", ge=0),
    limit: int = Query(100, description="Максимальное количество возвращаемых записей", le=1000),
    db: Session = Depends(get_db)
):
    """
    Получает список всех грузов на складе с поддержкой пагинации.
    """
    return db.query(models.Cargo).offset(skip).limit(limit).all()

@router.post(
    "/api/load",
    response_model=schemas.ShipmentResponse,
    tags=["shipments"],
    summary="Создать новую погрузку",
    response_description="Данные созданной погрузки",
    responses={
        200: {
            "description": "Погрузка успешно создана",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "starship_id": 1,
                        "cargo_id": 1,
                        "quantity": 50,
                        "status": "loading",
                        "created_at": "2024-03-20T10:30:00"
                    }
                }
            }
        },
        400: {
            "description": "Ошибка валидации",
            "content": {
                "application/json": {
                    "example": {"detail": "Превышена грузоподъемность звездолета"}
                }
            }
        },
        404: {"description": "Ресурс не найден"}
    }
)
@limiter.limit(RATE_LIMIT_PER_MINUTE["loading"])
async def load_cargo(
    request: Request,
    shipment: schemas.ShipmentCreate,
    db: Session = Depends(get_db)
):
    """
    Создает новую погрузку груза на звездолет.
    
    Проверяет:
    - Существование звездолета и груза
    - Доступность звездолета
    - Достаточность груза на складе
    - Не превышена ли грузоподъемность звездолета
    - Не превышен ли объем грузового отсека
    - Достаточно ли места с учетом уже загруженных грузов
    """
    # Проверяем существование звездолета
    starship = db.query(models.Starship).filter(models.Starship.id == shipment.starship_id).first()
    if not starship:
        raise HTTPException(status_code=404, detail="Звездолет не найден")
    
    # Проверяем статус звездолета
    if starship.status != schemas.StarshipStatus.AVAILABLE:
        raise HTTPException(status_code=400, detail="Звездолет недоступен для погрузки")
    
    # Проверяем существование груза
    cargo = db.query(models.Cargo).filter(models.Cargo.id == shipment.cargo_id).first()
    if not cargo:
        raise HTTPException(status_code=404, detail="Груз не найден")
    
    # Проверяем количество груза на складе
    if cargo.quantity < shipment.quantity:
        raise HTTPException(status_code=400, detail="Недостаточно груза на складе")
    
    # Получаем текущую загрузку звездолета
    current_shipments = db.query(models.ShipmentHistory).filter(
        models.ShipmentHistory.starship_id == starship.id,
        models.ShipmentHistory.status == schemas.ShipmentStatus.LOADING
    ).all()
    
    current_weight = sum(
        sh.quantity * db.query(models.Cargo).get(sh.cargo_id).weight 
        for sh in current_shipments
    )
    current_volume = sum(
        sh.quantity * db.query(models.Cargo).get(sh.cargo_id).volume 
        for sh in current_shipments
    )
    
    # Проверяем новый груз
    new_weight = shipment.quantity * cargo.weight
    new_volume = shipment.quantity * cargo.volume
    
    # Проверяем общий вес
    if current_weight + new_weight > starship.capacity:
        raise HTTPException(
            status_code=400, 
            detail=f"Превышена грузоподъемность звездолета. Доступно: {starship.capacity - current_weight} тонн"
        )
    
    # Проверяем общий объем
    if current_volume + new_volume > starship.volume:
        raise HTTPException(
            status_code=400, 
            detail=f"Превышен объем грузового отсека. Доступно: {starship.volume - current_volume} кубометров"
        )
    
    # Создаем запись о погрузке
    db_shipment = models.ShipmentHistory(
        starship_id=shipment.starship_id,
        cargo_id=shipment.cargo_id,
        quantity=shipment.quantity,
        status=schemas.ShipmentStatus.LOADING
    )
    
    # Обновляем количество груза и статус звездолета
    cargo.quantity -= shipment.quantity
    starship.status = schemas.StarshipStatus.LOADING
    
    db.add(db_shipment)
    db.commit()
    db.refresh(db_shipment)
    return db_shipment

@router.post(
    "/api/starships",
    response_model=schemas.Starship,
    tags=["starships"],
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый звездолет",
    response_description="Созданный звездолет",
    responses={
        400: {
            "description": "Ошибка валидации",
            "content": {
                "application/json": {
                    "example": {"detail": "Звездолет с таким именем уже существует"}
                }
            }
        }
    }
)
@limiter.limit(RATE_LIMIT_PER_MINUTE["starship_creation"])
async def create_starship(
    request: Request,
    starship: schemas.StarshipBase,
    db: Session = Depends(get_db)
):
    """
    Создает новый звездолет с указанными параметрами.
    
    - **name**: название звездолета (2-100 символов)
    - **capacity**: грузоподъемность в тоннах (0-1,000,000)
    - **range**: дальность полета в световых годах (0-10,000,000)
    """
    # Проверяем уникальность имени
    if db.query(models.Starship).filter(models.Starship.name == starship.name).first():
        raise HTTPException(status_code=400, detail="Звездолет с таким именем уже существует")
    
    db_starship = models.Starship(**starship.dict())
    db.add(db_starship)
    db.commit()
    db.refresh(db_starship)
    return db_starship

@router.get(
    "/api/starships/{starship_id}",
    response_model=schemas.Starship,
    tags=["starships"],
    summary="Получить информацию о конкретном звездолете"
)
def get_starship(
        starship_id: int = Path(..., description="ID звездолета"),
        db: Session = Depends(get_db)
):
    """
    Получает информацию о конкретном звездолете по его ID.
    """
    starship = db.query(models.Starship).filter(models.Starship.id == starship_id).first()
    if not starship:
        raise HTTPException(status_code=404, detail="Звездолет не найден")
    return starship

@router.put(
    "/api/starships/{starship_id}",
    response_model=schemas.Starship,
    tags=["starships"],
    summary="Обновить данные звездолета",
    responses={
        404: {"description": "Звездолет не найден"},
        400: {
            "description": "Ошибка валидации",
            "content": {
                "application/json": {
                    "example": {"detail": "Звездолет с таким именем уже существует"}
                }
            }
        }
    }
)
async def update_starship(
    request: Request,
    starship_id: int = Path(..., description="ID звездолета для обновления"),
    starship_update: schemas.StarshipBase = Body(..., description="Новые данные звездолета"),
    db: Session = Depends(get_db)
):
    """
    Обновляет данные существующего звездолета.
    
    - **name**: новое название звездолета (2-100 символов)
    - **capacity**: новая грузоподъемность в тоннах (0-1,000,000)
    - **range**: новая дальность полета в световых годах (0-10,000,000)
    
    Нельзя обновить звездолет, который находится в процессе погрузки или в полете.
    """
    db_starship = db.query(models.Starship).filter(models.Starship.id == starship_id).first()
    if not db_starship:
        raise HTTPException(status_code=404, detail="Звездолет не найден")
    
    if db_starship.status not in [schemas.StarshipStatus.AVAILABLE, schemas.StarshipStatus.MAINTENANCE]:
        raise HTTPException(status_code=400, detail="Нельзя изменять данные звездолета в процессе погрузки или в полете")
    
    # Проверяем уникальность имени, если оно меняется
    if starship_update.name != db_starship.name:
        existing = db.query(models.Starship).filter(models.Starship.name == starship_update.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Звездолет с таким именем уже существует")
    
    for key, value in starship_update.dict().items():
        setattr(db_starship, key, value)
    
    db.commit()
    db.refresh(db_starship)
    return db_starship

@router.delete(
    "/api/starships/{starship_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["starships"],
    summary="Удалить звездолет",
    responses={
        404: {"description": "Звездолет не найден"},
        400: {
            "description": "Ошибка валидации",
            "content": {
                "application/json": {
                    "example": {"detail": "Нельзя удалить звездолет, который используется"}
                }
            }
        }
    }
)
async def delete_starship(
    request: Request,
    starship_id: int = Path(..., description="ID звездолета для удаления"),
    db: Session = Depends(get_db)
):
    """
    Удаляет звездолет из системы.
    
    Нельзя удалить звездолет, который:
    - Находится в процессе погрузки
    - Находится в полете
    - Имеет историю погрузок
    """
    db_starship = db.query(models.Starship).filter(models.Starship.id == starship_id).first()
    if not db_starship:
        raise HTTPException(status_code=404, detail="Звездолет не найден")
    
    if db_starship.status not in [schemas.StarshipStatus.AVAILABLE, schemas.StarshipStatus.MAINTENANCE]:
        raise HTTPException(status_code=400, detail="Нельзя удалить звездолет в процессе погрузки или в полете")
    
    # Проверяем наличие истории погрузок
    shipment_history = db.query(models.ShipmentHistory).filter(
        models.ShipmentHistory.starship_id == starship_id
    ).first()
    
    if shipment_history:
        raise HTTPException(status_code=400, detail="Нельзя удалить звездолет, у которого есть история погрузок")
    
    db.delete(db_starship)
    db.commit()
    return None

@router.post(
    "/api/cargo",
    response_model=schemas.Cargo,
    tags=["cargo"],
    status_code=status.HTTP_201_CREATED,
    summary="Добавить новый груз на склад"
)
def create_cargo(
    request: Request,
    cargo: schemas.CargoCreate = Body(...),
    db: Session = Depends(get_db)
):
    """
    Добавляет новый тип груза на склад.
    """
    existing = db.query(models.Cargo).filter(models.Cargo.name == cargo.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Груз с таким названием уже существует")
    db_cargo = models.Cargo(**cargo.dict())
    db.add(db_cargo)
    db.commit()
    db.refresh(db_cargo)
    return db_cargo

@router.put(
    "/api/cargo/{cargo_id}",
    response_model=schemas.Cargo,
    tags=["cargo"],
    summary="Обновить данные груза",
    responses={
        404: {"description": "Груз не найден"},
        400: {
            "description": "Ошибка валидации",
            "content": {
                "application/json": {
                    "example": {"detail": "Груз с таким названием уже существует"}
                }
            }
        }
    }
)
async def update_cargo(
    request: Request,
    cargo_id: int = Path(..., description="ID груза для обновления"),
    cargo_update: schemas.CargoBase = Body(..., description="Новые данные груза"),
    db: Session = Depends(get_db)
):
    """
    Обновляет данные существующего груза.
    
    - **name**: новое название груза (2-100 символов)
    - **quantity**: новое количество (0-1,000,000)
    - **weight**: новый вес единицы в тоннах (0-1,000)
    - **volume**: новый объем единицы в кубических метрах (0-1,000)
    """
    db_cargo = db.query(models.Cargo).filter(models.Cargo.id == cargo_id).first()
    if not db_cargo:
        raise HTTPException(status_code=404, detail="Груз не найден")
    
    # Проверяем уникальность имени, если оно меняется
    if cargo_update.name != db_cargo.name:
        existing = db.query(models.Cargo).filter(models.Cargo.name == cargo_update.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Груз с таким названием уже существует")
    
    for key, value in cargo_update.dict().items():
        setattr(db_cargo, key, value)
    
    db.commit()
    db.refresh(db_cargo)
    return db_cargo

@router.delete(
    "/api/cargo/{cargo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["cargo"],
    summary="Удалить груз",
    responses={
        404: {"description": "Груз не найден"},
        400: {
            "description": "Ошибка валидации",
            "content": {
                "application/json": {
                    "example": {"detail": "Нельзя удалить груз, который используется"}
                }
            }
        }
    }
)
async def delete_cargo(
    request: Request,
    cargo_id: int = Path(..., description="ID груза для удаления"),
    db: Session = Depends(get_db)
):
    """
    Удаляет груз из системы.
    
    Нельзя удалить груз, который:
    - Используется в текущих погрузках
    - Имеет историю погрузок
    """
    db_cargo = db.query(models.Cargo).filter(models.Cargo.id == cargo_id).first()
    if not db_cargo:
        raise HTTPException(status_code=404, detail="Груз не найден")
    
    # Проверяем наличие истории погрузок
    shipment_history = db.query(models.ShipmentHistory).filter(
        models.ShipmentHistory.cargo_id == cargo_id
    ).first()
    
    if shipment_history:
        raise HTTPException(status_code=400, detail="Нельзя удалить груз, который использовался в погрузках")
    
    db.delete(db_cargo)
    db.commit()
    return None

@router.get(
    "/api/starships/available",
    response_model=List[schemas.Starship],
    summary="Получить список доступных звездолетов",
    tags=["starships"]
)
def get_available_starships(
        min_capacity: Optional[float] = Query(None, description="Минимальная грузоподъемность в кг"),
        min_range: Optional[float] = Query(None, description="Минимальная дальность полета в км"),
        db: Session = Depends(get_db)
):
    """
    Возвращает список звездолетов, доступных для погрузки.
    """
    try:
        query = db.query(models.Starship).filter(models.Starship.status == schemas.StarshipStatus.AVAILABLE)

        if min_capacity is not None:
            if min_capacity < 0:
                raise HTTPException(status_code=400, detail="Минимальная грузоподъемность не может быть отрицательной")
            query = query.filter(models.Starship.capacity >= min_capacity)

        if min_range is not None:
            if min_range < 0:
                raise HTTPException(status_code=400, detail="Минимальная дальность не может быть отрицательной")
            query = query.filter(models.Starship.range >= min_range)

        return query.all()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Ошибка при получении списка звездолетов")

@router.get(
    "/api/history",
    response_model=List[schemas.ShipmentResponse],
    tags=["history"],
    summary="Получить историю погрузок"
)
@limiter.limit(RATE_LIMIT_PER_MINUTE["history"])
def get_shipment_history(
    request: Request,
    starship_id: Optional[int] = Query(None, description="Фильтр по ID звездолета"),
    cargo_id: Optional[int] = Query(None, description="Фильтр по ID груза"),
    status: Optional[schemas.ShipmentStatus] = Query(None, description="Фильтр по статусу"),
    from_date: Optional[datetime] = Query(None, description="Начальная дата (YYYY-MM-DD)"),
    to_date: Optional[datetime] = Query(None, description="Конечная дата (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Получает историю погрузок с возможностью фильтрации.
    """
    query = db.query(models.ShipmentHistory)

    if starship_id:
        query = query.filter(models.ShipmentHistory.starship_id == starship_id)
    if cargo_id:
        query = query.filter(models.ShipmentHistory.cargo_id == cargo_id)
    if status:
        query = query.filter(models.ShipmentHistory.status == status)
    if from_date:
        query = query.filter(models.ShipmentHistory.created_at >= from_date)
    if to_date:
        query = query.filter(models.ShipmentHistory.created_at <= to_date)

    return query.order_by(models.ShipmentHistory.created_at.desc()).all()

@router.post(
    "/api/load/cancel/{shipment_id}",
    response_model=schemas.ShipmentResponse,
    tags=["shipments"],
    summary="Отменить погрузку"
)
def cancel_loading(
    request: Request,
    shipment_id: int = Path(..., description="ID погрузки для отмены"),
    db: Session = Depends(get_db)
):
    """
    Отменяет процесс погрузки и возвращает груз на склад.
    """
    try:
        shipment = db.query(models.ShipmentHistory).filter(models.ShipmentHistory.id == shipment_id).first()
        if not shipment:
            raise HTTPException(status_code=404, detail="Погрузка не найдена")

        if shipment.status != schemas.ShipmentStatus.LOADING:
            raise HTTPException(status_code=400, detail="Можно отменить только погрузки в статусе 'loading'")

        cargo = db.query(models.Cargo).filter(models.Cargo.id == shipment.cargo_id).first()
        if not cargo:
            raise HTTPException(status_code=404, detail="Груз не найден")
        cargo.quantity += shipment.quantity

        starship = db.query(models.Starship).filter(models.Starship.id == shipment.starship_id).first()
        if not starship:
            raise HTTPException(status_code=404, detail="Звездолет не найден")
        starship.status = schemas.StarshipStatus.AVAILABLE

        shipment.status = schemas.ShipmentStatus.CANCELLED

        db.commit()
        db.refresh(shipment)
        return shipment
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Произошла ошибка при отмене погрузки"
        )

@router.get(
    "/api/starships/{starship_id}/load",
    tags=["starships"],
    summary="Получить информацию о текущей загрузке звездолета"
)
async def get_starship_load(
    request: Request,
    starship_id: int = Path(..., description="ID звездолета"),
    db: Session = Depends(get_db)
):
    """
    Возвращает информацию о текущей загрузке звездолета:
    - Общий вес груза
    - Общий объем груза
    - Оставшаяся грузоподъемность
    - Оставшийся объем
    - Список загруженных грузов
    """
    starship = db.query(models.Starship).filter(models.Starship.id == starship_id).first()
    if not starship:
        raise HTTPException(status_code=404, detail="Звездолет не найден")
    
    current_shipments = db.query(models.ShipmentHistory).filter(
        models.ShipmentHistory.starship_id == starship.id,
        models.ShipmentHistory.status == schemas.ShipmentStatus.LOADING
    ).all()
    
    current_weight = sum(
        sh.quantity * db.query(models.Cargo).get(sh.cargo_id).weight 
        for sh in current_shipments
    )
    current_volume = sum(
        sh.quantity * db.query(models.Cargo).get(sh.cargo_id).volume 
        for sh in current_shipments
    )
    
    return {
        "starship_name": starship.name,
        "total_capacity": starship.capacity,
        "total_volume": starship.volume,
        "current_weight": current_weight,
        "current_volume": current_volume,
        "available_weight": starship.capacity - current_weight,
        "available_volume": starship.volume - current_volume,
        "loaded_cargo": [
            {
                "cargo_name": db.query(models.Cargo).get(sh.cargo_id).name,
                "quantity": sh.quantity,
                "weight": sh.quantity * db.query(models.Cargo).get(sh.cargo_id).weight,
                "volume": sh.quantity * db.query(models.Cargo).get(sh.cargo_id).volume
            }
            for sh in current_shipments
        ]
    } 