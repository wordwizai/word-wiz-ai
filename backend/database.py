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
# RDS drops connections that sit idle, and the pool would hand the dead one to
# the next request, which then failed with "MySQL server has gone away".
# pool_pre_ping tests a connection before use and replaces it if it is dead.
engine = create_engine(
    URL_DATABASE,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_recycle=1800,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
metadata = MetaData()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


Base = declarative_base()
