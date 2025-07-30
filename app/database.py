from sqlmodel import create_engine, Session
from .core.config import settings


# SQLAlchemy 엔진
mysql_url = settings.DATABASE_URL
engine = create_engine(mysql_url, echo=True, isolation_level="READ COMMITTED")


def get_db():
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()
