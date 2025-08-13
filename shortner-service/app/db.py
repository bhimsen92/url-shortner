from functools import wraps

from sqlalchemy.orm import scoped_session, sessionmaker
from sqlmodel import create_engine

from app.config import settings

engine = create_engine(
    url=settings.sqlalchemy_database_uri,
    pool_pre_ping=True,
)

SessionFactory = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

Session: scoped_session = scoped_session(SessionFactory)


def atomic(func):
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        session = Session()
        try:
            with session.begin():
                return func(*args, **kwargs)
        finally:
            session.remove()

    return sync_wrapper
