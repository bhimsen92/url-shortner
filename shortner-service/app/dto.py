from datetime import datetime

from pydantic import BaseModel


class UserLogin(BaseModel):
    username: str
    password: str


class UserSignUp(UserLogin):
    display_name: str


class Token(BaseModel):
    access_token: str


class URLIn(BaseModel):
    original_url: str
    alias: str
    expires_in: datetime


class URLOut(BaseModel):
    short_url: str
