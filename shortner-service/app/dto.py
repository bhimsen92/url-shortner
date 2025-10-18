from datetime import datetime

from pydantic import BaseModel, ConfigDict


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


class URLItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    original_url: str
    expires_at: datetime | None = None
    short_url: str


class ClickCount(BaseModel):
    short_url: str
    country_code: str
    counts: int


class ClickStreamMessage(BaseModel):
    message_id: str
    short_url: str
    request_ip: str
