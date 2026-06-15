from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
from config import DATABASE_URL

# create_engine не открывает соединение немедленно — это безопасно при импорте.
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_models():
    """Создаёт таблицы при старте приложения.

    Раньше create_all вызывался прямо на этапе импорта модуля. Из-за этого
    любая проблема с БД (недоступна, не задан DATABASE_URL) роняла весь
    процесс ещё до запуска сервера — Railway отвечал 502 'Application failed
    to respond' на ВСЕ адреса, включая /docs. Теперь инициализация вынесена
    в startup-хендлер и обёрнута в try/except (см. main.py), поэтому даже при
    недоступной БД приложение поднимается и отдаёт /docs и /health.
    """
    Base.metadata.create_all(bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
