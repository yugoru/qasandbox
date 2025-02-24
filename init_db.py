from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.models import Base, Starship, Cargo, ShipmentHistory
from app.schemas import StarshipStatus, ShipmentStatus
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


# Функция для создания тестовых данных
def create_test_data(db):
    try:
        # Создаем тестовые звездолеты
        starships = [
            Starship(
                name="Millennium Falcon",
                capacity=100000,
                volume=50000,
                range=1000000,
                status=StarshipStatus.AVAILABLE
            ),
            Starship(
                name="Battlestar Galactica",
                capacity=500000,
                volume=250000,
                range=2000000,
                status=StarshipStatus.MAINTENANCE
            ),
            Starship(
                name="USS Enterprise",
                capacity=300000,
                volume=150000,
                range=1500000,
                status=StarshipStatus.AVAILABLE
            )
        ]

        # Создаем тестовые грузы
        cargos = [
            Cargo(
                name="Dilithium Crystals",
                quantity=1000,
                weight=10.5,
                volume=2.3
            ),
            Cargo(
                name="Quantum Torpedoes",
                quantity=500,
                weight=50.0,
                volume=10.0
            ),
            Cargo(
                name="Medical Supplies",
                quantity=2000,
                weight=5.0,
                volume=8.0
            )
        ]

        # Добавляем данные в базу
        for starship in starships:
            db.add(starship)
        for cargo in cargos:
            db.add(cargo)

        # Создаем тестовую историю погрузок
        db.commit()  # Коммитим чтобы получить ID созданных объектов

        shipments = [
            ShipmentHistory(
                starship_id=1,
                cargo_id=1,
                quantity=100,
                status=ShipmentStatus.COMPLETED
            ),
            ShipmentHistory(
                starship_id=3,
                cargo_id=2,
                quantity=50,
                status=ShipmentStatus.LOADING
            ),
            ShipmentHistory(
                starship_id=1,
                cargo_id=3,
                quantity=200,
                status=ShipmentStatus.CANCELLED
            )
        ]

        for shipment in shipments:
            db.add(shipment)

        db.commit()
        print("Тестовые данные успешно созданы")

    except Exception as e:
        db.rollback()
        print(f"Ошибка при создании тестовых данных: {e}")
        raise


# Функция для создания таблиц и тестовых данных
def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        print("Таблицы успешно созданы.")

        # Создаем сессию и добавляем тестовые данные
        db = SessionLocal()
        create_test_data(db)
        db.close()

    except Exception as e:
        print(f"Ошибка при инициализации базы данных: {e}")
        raise


# Запуск инициализации базы данных
if __name__ == "__main__":
    init_db()
