from fastapi.openapi.utils import get_openapi
from config import CORS_ORIGINS, PROJECT_NAME, VERSION

origins = CORS_ORIGINS

def custom_openapi(app):
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=PROJECT_NAME,
        version=VERSION,
        description="""
        # Управление космическим складом 🚀
        
        Это API предоставляет функционал для:
        
        ## Звездолеты
        * Просмотр списка доступных звездолетов
        * Управление характеристиками звездолетов
        * Отслеживание статуса звездолетов
        
        ## Грузы
        * Управление инвентарем склада
        * Отслеживание количества грузов
        * Контроль веса и объема
        
        ## Погрузка
        * Создание заявок на погрузку
        * Отмена погрузки
        * История операций
        
        ## Статусы звездолетов
        * `available` - доступен для погрузки
        * `maintenance` - на техобслуживании
        * `in_flight` - в полете
        * `loading` - идет погрузка
        
        ## Аутоматическая очистка
        Система автоматически очищает:
        * Записи истории старше 24 часов
        * Зависшие погрузки
        """,
        routes=app.routes,
    )

    # Добавляем примеры для некоторых схем
    openapi_schema["components"]["schemas"]["Starship"]["example"] = {
        "id": 1,
        "name": "Millennium Falcon",
        "capacity": 100000,
        "range": 1000000,
        "status": "available"
    }

    openapi_schema["components"]["schemas"]["Cargo"]["example"] = {
        "id": 1,
        "name": "Dilithium Crystals",
        "quantity": 100,
        "weight": 10.5,
        "volume": 2.3
    }

    openapi_schema["components"]["schemas"]["ShipmentResponse"]["example"] = {
        "id": 1,
        "starship_id": 1,
        "cargo_id": 1,
        "quantity": 50,
        "status": "loading",
        "created_at": "2024-03-20T10:30:00"
    }

    # Добавляем теги для группировки эндпоинтов
    openapi_schema["tags"] = [
        {
            "name": "starships",
            "description": "Операции со звездолетами"
        },
        {
            "name": "cargo",
            "description": "Операции с грузами"
        },
        {
            "name": "shipments",
            "description": "Операции с погрузками"
        },
        {
            "name": "history",
            "description": "История операций"
        }
    ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema
