from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError

from app.config import settings
from app.db import Session, engine, session_ctx
from app.exceptions import NotFound
from app.models import User
from app.security import decode_jwt
from app.service import CounterService, URLService, UserService

oauth_extractor = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1}/users/access-token",
)
TokenDep = Annotated[str, Depends(oauth_extractor)]


counter_service = CounterService(
    key=settings.id_counter_key,
    batch_size=settings.id_counter_batch_size,
    context=session_ctx,
)
user_service = UserService(context=session_ctx)
url_service = URLService(
    counter_service=counter_service,
    hash_id_secret=settings.hash_id_counter_secret,
    context=session_ctx,
)


# implement session code.
async def get_session():
    with Session(engine, autoflush=True) as session:
        token = session_ctx.set(session)
        yield session
        session_ctx.reset(token)


SessionDep = Annotated[Session, Depends(get_session)]


def get_current_user(_: SessionDep, token: TokenDep) -> User:
    sub: str = ""
    try:
        payload: dict = decode_jwt(token)
        sub: str = payload["sub"]
    except (InvalidTokenError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials.",
        )

    try:
        user: User = user_service.get_user(user_id=sub)
    except NotFound:
        raise HTTPException(status_code=404, detail="user not found.")

    if not user.is_active:
        raise HTTPException(status_code=400, detail="inactive user.")

    return user


# simple utility functions.
def get_user_service(session: SessionDep) -> UserService:
    return user_service


def get_url_service(session: SessionDep) -> URLService:
    return url_service


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
URLServiceDep = Annotated[URLService, Depends(get_url_service)]
CurrentUser = Annotated[User, Depends(get_current_user)]
