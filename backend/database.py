from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker

from sqlalchemy.ext.declarative import declarative_base
import os
import dotenv


dotenv.load_dotenv()
URL_DATABASE = os.getenv("DATABASE_URL", "")

# SQLite (the local dev server, see dev_server.py) has to share connections
# across FastAPI's threadpool; MySQL needs no extra arguments.
connect_args = (
    {"check_same_thread": False} if URL_DATABASE.startswith("sqlite") else {}
)
engine = create_engine(URL_DATABASE, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
metadata = MetaData()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


Base = declarative_base()
