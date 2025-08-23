import dotenv
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker

from sqlalchemy.ext.declarative import declarative_base
import os

dotenv.load_dotenv()
URL_DATABASE = os.getenv("DATABASE_URL", "")

engine = create_engine(URL_DATABASE)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
metadata = MetaData()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


Base = declarative_base()
