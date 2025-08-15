from pydantic import BaseModel
from typing import Optional


class User(BaseModel):
    display_name: str
    username: str
    is_active: bool


class UserIn(BaseModel):
    username: str
    password: str


class UserCreate(UserIn):
    display_name: str


class ShortenRequest(BaseModel):
    original_url: str
    alias: Optional[str] = None
    expiry_seconds: Optional[int] = None


class URLItem(ShortenRequest):
    short_url: str
