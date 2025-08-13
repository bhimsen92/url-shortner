import uuid
from datetime import datetime

from passlib.context import CryptContext
from sqlmodel import Field, Relationship, SQLModel

from app.security import encode_jwt

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    username: str = Field(index=True)
    display_name: str
    hashed_password: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # back-populate fields.
    url: list["URL"] = Relationship(back_populates="user")

    def set_password(self, raw_password: str) -> None:
        self.hashed_password = pwd_context.hash(raw_password)

    def verify_password(self, raw_password) -> bool:
        return pwd_context.verify(raw_password, self.hashed_password)

    def token(self):
        payload = {
            "sub": self.id,
        }
        return encode_jwt(payload=payload)


class URL(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    original_url: str
    short_url: str
    created_by: uuid.UUID = Field(foreign_key="user.id")
    expires_at: datetime = Field(default=None)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # back-populate fields.
    user: User = Relationship(back_populates="urls")
