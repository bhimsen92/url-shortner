from contextvars import ContextVar

from sqlmodel import Session, create_engine

from app.config import settings

engine = create_engine(
    url=settings.sqlalchemy_database_uri,
    pool_pre_ping=True,
)


_session_ctx: ContextVar[Session] = ContextVar("session_ctx")


class SessionContext:
    def __init__(self, atomic: bool = True):
        # TODO: is atomic the right property name ?
        self.atomic = True
        self.session: Session | None = None
        self._token = None

    def __enter__(self) -> Session:
        self.session = Session(engine, autoflush=True, autocommit=False)
        self._token = _session_ctx.set(self.session)

        if self.atomic:
            self.session.begin()

        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.atomic and self.session:
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
