from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.models import Base
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

# Получаем URL подключения из переменной окружения
DATABASE_URL = os.getenv("DATABASE_URL")

# Проверяем, корректно ли загружена строка подключения
if not DATABASE_URL:
    raise ValueError("Переменная окружения DATABASE_URL не установлена!")

# Создаем подключение к базе данных
try:
    engine = create_engine(
        DATABASE_URL,
        echo=True,
        future=True,
        connect_args={
            "client_encoding": "utf8"
        }
    )
    
    # Устанавливаем кодировку для соединения
    @event.listens_for(engine, 'connect')
    def set_encoding(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute('SET client_encoding TO utf8')
        cursor.close()
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    print(f"Ошибка при подключении к базе данных: {e}")
    raise

# Функция для создания таблиц
def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        print("Таблицы успешно созданы.")
    except Exception as e:
        print(f"Ошибка при создании таблиц: {e}")
        raise

# Запуск инициализации базы данных
if __name__ == "__main__":
    init_db()
