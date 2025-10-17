from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError

from app.config import settings
from app.db import Session, SessionContext
from app.exceptions import NotFound
from app.models import User
from app.security import decode_jwt
from app.service import URLService, UserService


async def session_with_transaction():
    with SessionContext(with_transaction=True) as session:
        yield session


async def session_without_transaction():
    # without transaction session simply gives you a session context, does not explicitly
    # start a session. so its user should manage the beginning/commit/rollback on their own.
    return SessionContext(with_transaction=False)


# simple utility functions.
def get_user_service(request: Request) -> UserService:
    return request.state.user_service


def get_url_service(request: Request) -> URLService:
    return request.state.url_service


# dependency setup.

oauth_extractor = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1}/users/access-token",
)
TokenDep = Annotated[str, Depends(oauth_extractor)]


SessionDep = Annotated[Session, Depends(session_with_transaction)]


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
URLServiceDep = Annotated[URLService, Depends(get_url_service)]


def get_current_user(
    user_service: UserServiceDep, _: SessionDep, token: TokenDep
) -> User:
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


CurrentUser = Annotated[User, Depends(get_current_user)]
