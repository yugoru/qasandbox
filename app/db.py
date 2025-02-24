from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
from config import DATABASE_URL

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
