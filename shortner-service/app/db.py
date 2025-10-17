from contextvars import ContextVar

from sqlalchemy import Engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, create_engine

_sessionmakers: sessionmaker[Session] = None
_session_ctx: ContextVar[Session] = ContextVar("session_ctx")


def setup_postgresql(settings):
    global _sessionmakers

    engine = create_engine(
        url=settings.sqlalchemy_database_uri,
        pool_pre_ping=True,
    )

    # set the global variable.
    _sessionmakers = sessionmaker(
        bind=engine,
        class_=Session,
        autoflush=True,
        autocommit=False,
    )

    return _sessionmakers


def close_db_connections():
    engine: Engine = _sessionmakers.kw["bind"]
    engine.dispose()


class SessionContext:
    def __init__(self, with_transaction: bool = True):
        self.with_transaction = with_transaction
        self.session: Session | None = None
        self._token = None

    def __enter__(self) -> Session:
        assert _sessionmakers, "Please setup database before using SessionContext"

        self.session: Session = _sessionmakers()
        self._token = _session_ctx.set(self.session)

        if self.with_transaction:
            self.session.begin()

        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.with_transaction and self.session:
            if exc_type:
                self.session.rollback()
            else:
                self.session.commit()

        _session_ctx.reset(self._token)
        if self.session:
            self.session.close()


# Helper to pull the current session. This will be used by services.
class CurrentSessionContext:
    @property
    def session(self) -> Session:
        try:
            return _session_ctx.get()
        except LookupError:
            raise RuntimeError("No session found in context")


current_ctx = CurrentSessionContext()
