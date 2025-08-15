# app/auth.py
from itsdangerous import URLSafeSerializer, BadSignature
from fastapi import Response
from .config import settings
from typing import Optional, Dict
import secrets

_serializer = URLSafeSerializer(settings.secret_key, salt="ui-session")
_csrf_serializer = URLSafeSerializer(settings.secret_key, salt="ui-csrf")


def create_session_cookie(user_payload: Dict[str, str]) -> str:
    return _serializer.dumps(user_payload)


def decode_session_cookie(cookie_value: str) -> Optional[Dict[str, str]]:
    try:
        return _serializer.loads(cookie_value)
    except BadSignature:
        return None


def set_session(response: Response, cookie_value: str) -> None:
    response.set_cookie(
        settings.session_cookie,
        cookie_value,
        max_age=settings.cookie_max_age,
        httponly=True,
        samesite="lax",
        secure=True,  # set True in prod
        path="/",
    )


def clear_session(response: Response) -> None:
    response.delete_cookie(settings.session_cookie, path="/")


# --- CSRF token helpers ---


def _generate_csrf_value() -> str:
    return secrets.token_urlsafe(32)


def create_csrf_cookie() -> str:
    raw = _generate_csrf_value()
    return _csrf_serializer.dumps({"csrf": raw})


def verify_csrf_token(signed_token: str, presented_token: str) -> bool:
    if not signed_token or not presented_token:
        return False
    try:
        obj = _csrf_serializer.loads(signed_token)
        return obj.get("csrf") == presented_token
    except BadSignature:
        return False


def set_csrf_cookie(response: Response) -> None:
    signed = create_csrf_cookie()
    response.set_cookie(
        "ui_csrf",
        signed,
        max_age=settings.COOKIE_MAX_AGE,
        httponly=False,  # readable by JS
        samesite="lax",
        secure=False,
        path="/",
    )


def clear_csrf_cookie(response: Response) -> None:
    response.delete_cookie("ui_csrf", path="/")
