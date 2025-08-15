from contextvars import ContextVar
from functools import wraps
from typing import Any

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


_session_ctx: ContextVar[Session] = ContextVar("session_ctx")


class SessionContext:
    @property
    def session(self) -> Session:
        try:
            return _session_ctx.get()
        except LookupError:
            raise RuntimeError("No session found in context")

    def set(self, session: Session) -> Any:
        return _session_ctx.set(session)

    def reset(self, token):
        _session_ctx.reset(token)


session_ctx = SessionContext()
