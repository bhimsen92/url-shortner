from datetime import datetime, timedelta

import jwt

from app.config import settings


def encode_jwt(payload):
    expiry_time = datetime.now() + timedelta(
        minutes=settings.jwt_expire_duration_minutes
    )
    to_encode = {
        **payload,
        "exp": expiry_time,
    }

    token = jwt.encode(
        to_encode,
        settings.jwt_secret,
        [settings.jwt_algorithm],
    )
    return token


def decode_jwt(token: str) -> dict:
    payload = jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
    )
    return payload
