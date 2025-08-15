import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.dependencies import SessionDep, UserServiceDep, get_current_user
from app.dto import Token, UserCreate, UserLogin, UserOut
from app.exceptions import NotFound
from app.models import User

LOG = logging.getLogger(__file__)


route = APIRouter(
    prefix="/users",
    tags=["users"],
)


@route.post("/")
def create_user(
    user_create: UserCreate,
    session: SessionDep,
    user_service: UserServiceDep,
) -> Token:
    try:
        user = user_service.create_user(user_data=user_create)
        return Token(access_token=user.token())
    except IntegrityError as _:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with username: {user_create.username} already exists.",
        )


@route.get("/me", response_model=UserOut)
def get_user(user: Annotated[User, Depends(get_current_user)]) -> Any:
    return user


@route.post("/access-token")
def get_token(
    user_login: UserLogin, session: SessionDep, user_service: UserServiceDep
) -> Token:
    try:
        return user_service.create_token(user_data=user_login)
    except NotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
