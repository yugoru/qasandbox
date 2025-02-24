import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Database
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set in environment variables")

# API Settings
API_V1_STR = "/api"
PROJECT_NAME = "Starship Warehouse API"
VERSION = "1.0.0"

# CORS Settings
CORS_ORIGINS = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:3000",
    os.getenv("WORDPRESS_URL", "http://localhost:8080"),
]

# Rate Limiting
RATE_LIMIT_PER_MINUTE = {
    "default": "100/minute",
    "starship_creation": "20/minute",
    "loading": "30/minute",
    "history": "200/minute",
}

# Cleanup Settings
CLEANUP_HISTORY_DAYS = 1  # Количество дней хранения истории
STUCK_LOADING_HOURS = 1   # Количество часов до освобождения "зависших" кораблей

# Server Settings
HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", 8000)) 