from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError

from app.config import settings
from app.db import Session, SessionContext, current_ctx
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
    context=current_ctx,
)
user_service = UserService(context=current_ctx)
url_service = URLService(
    counter_service=counter_service,
    hash_id_secret=settings.hash_id_counter_secret,
    context=current_ctx,
)


async def atomic_session():
    with SessionContext(atomic=True) as session:
        yield session


async def non_atomic_session():
    # atomic session simply gives you a session context, does not explicitly start a session.
    # so its user should manage the beginning/commit/rollback on their own.
    return SessionContext(atomic=False)


SessionDep = Annotated[Session, Depends(atomic_session)]


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
def get_user_service() -> UserService:
    return user_service


def get_url_service() -> URLService:
    return url_service


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
URLServiceDep = Annotated[URLService, Depends(get_url_service)]
CurrentUser = Annotated[User, Depends(get_current_user)]
