import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel

from app.security import encode_jwt, validate_password


class User(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str = Field(index=True, unique=True)
    display_name: str
    hashed_password: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # back-populate fields.
    urls: list["URL"] = Relationship(back_populates="user")

    def verify_password(self, raw_password) -> bool:
        return validate_password(raw_password, self.hashed_password)

    def token(self):
        payload = {
            "sub": str(self.id),
        }
        return encode_jwt(payload=payload)


class URL(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    original_url: str
    short_url: str = Field(index=True, unique=True)
    created_by: uuid.UUID = Field(foreign_key="user.id")
    expires_at: Optional[datetime] = Field(default=None, nullable=True)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # back-populate fields.
    user: User = Relationship(back_populates="urls")


class IDCounter(SQLModel, table=True):
    key: str = Field(primary_key=True, index=True)
    next_id: int = Field(default=1, nullable=False)
