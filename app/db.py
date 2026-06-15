from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
from config import DATABASE_URL

# create_engine не открывает соединение немедленно — это безопасно при импорте.
# Если DATABASE_URL не задан, не падаем при импорте: движок будет None, а
# get_db вернёт понятную 503.
engine = create_engine(DATABASE_URL) if DATABASE_URL else None

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None


def init_models():
    """Создаёт таблицы при старте приложения.

    Раньше create_all вызывался прямо на этапе импорта модуля. Из-за этого
    любая проблема с БД (недоступна, не задан DATABASE_URL) роняла весь
    процесс ещё до запуска сервера — Railway отвечал 502 'Application failed
    to respond' на ВСЕ адреса, включая /docs. Теперь инициализация вынесена
    в startup-хендлер и обёрнута в try/except (см. main.py), поэтому даже при
    недоступной БД приложение поднимается и отдаёт /docs и /health.
    """
    if engine is None:
        raise RuntimeError("DATABASE_URL не задан — нечего инициализировать")
    Base.metadata.create_all(bind=engine)

# Dependency
def get_db():
    if SessionLocal is None:
        raise HTTPException(
            status_code=503,
            detail="База данных не настроена: не задан DATABASE_URL",
        )
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
