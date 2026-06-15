import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Загружаем переменные окружения
load_dotenv()

# Настройки сервера
HOST = "0.0.0.0"  # Для Railway нужно использовать 0.0.0.0
PORT = int(os.getenv("PORT", 8080))  # Railway предоставляет порт через переменную окружения

# Database
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Раньше тут был raise ValueError, который ронял процесс на этапе импорта
    # (и Railway отдавал 502 на все адреса, включая /docs). Теперь только
    # предупреждаем: приложение поднимется и отдаст /docs и /health, а
    # БД-эндпоинты вернут понятную 503.
    logger.warning("DATABASE_URL не задан — эндпоинты, работающие с БД, будут недоступны")

# CORS
CORS_ORIGINS = [
    "http://localhost",
    "http://localhost:8080",
    "https://localhost",
    "https://localhost:8080",
    "*",  # Для тестирования, в продакшене лучше указать конкретные домены
]

# Project
PROJECT_NAME = "Starship Warehouse API"
VERSION = "1.0.0"

# Rate Limiting
RATE_LIMIT_PER_MINUTE = {
    "default": "100/minute",
    "starship_creation": "20/minute",
    "loading": "30/minute",
    "history": "200/minute"
}

# Cleanup Settings
CLEANUP_HISTORY_DAYS = 1  # Количество дней хранения истории
STUCK_LOADING_HOURS = 1   # Количество часов до освобождения "зависших" кораблей

# API Settings
API_V1_STR = "/api"

# API Security Settings
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

if TEST_MODE:
    print("WARNING: Running in TEST_MODE. Token verification is disabled!") 