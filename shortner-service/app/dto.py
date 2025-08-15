from datetime import datetime

from pydantic import BaseModel


class UserLogin(BaseModel):
    username: str
    password: str


class UserCreate(UserLogin):
    display_name: str


class UserOut(BaseModel):
    username: str
    display_name: str
    is_active: bool


class Token(BaseModel):
    access_token: str


class URLIn(BaseModel):
    original_url: str
    alias: str | None = None
    expires_in: datetime | None = None


class URLOut(BaseModel):
    short_url: str
