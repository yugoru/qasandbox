from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api import custom_openapi
from app.middleware import log_requests_middleware
from app.exceptions import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from app.limiter import limiter
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from config import HOST, PORT, CORS_ORIGINS, PROJECT_NAME, VERSION
import logging

logger = logging.getLogger(__name__)

# Создаем приложение
app = FastAPI()

# Регистрируем лимитер
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Регистрируем обработчики ошибок
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Регистрируем middleware
app.middleware("http")(log_requests_middleware)

# Настраиваем OpenAPI
app.openapi = lambda: custom_openapi(app)

# Настраиваем CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
    max_age=3600,
)

# Импортируем все роуты
from app.routes import router
app.include_router(router)


# Инициализация БД при старте — отказоустойчиво.
# Если БД недоступна, приложение всё равно поднимется (отдаст /docs и /health),
# а не упадёт целиком с 502 на этапе импорта.
from app.db import init_models


@app.on_event("startup")
def on_startup():
    try:
        init_models()
        logger.info("База данных инициализирована успешно")
    except Exception:
        logger.exception(
            "Не удалось инициализировать БД при старте. Приложение поднято, "
            "но эндпоинты, работающие с БД, будут возвращать ошибки."
        )


@app.get("/", include_in_schema=False)
def root():
    """Корень сервиса — короткая навигация."""
    return {
        "service": PROJECT_NAME,
        "version": VERSION,
        "docs": "/docs",
        "openapi": "/openapi.json",
        "health": "/health",
    }


@app.get("/health", tags=["service"], summary="Проверка живости сервиса")
def health():
    """Liveness-проба для Railway. Не обращается к БД, поэтому отвечает 200,
    даже если база временно недоступна — это позволяет деплою пройти."""
    return {"status": "ok"}


# Если запускаем напрямую
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=False  # На продакшене отключаем автоперезагрузку
    )
