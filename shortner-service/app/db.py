from functools import wraps

from sqlmodel import Session, create_engine

from app.config import settings

engine = create_engine(
    url=settings.sqlalchemy_database_uri,
    pool_pre_ping=True,
)


def atomic(func):
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        session = Session(engine, autoflush=True, autocommit=False)
        try:
            with session.begin():
                return func(*args, **kwargs)
        finally:
            session.close()

    return sync_wrapper
