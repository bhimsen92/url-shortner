from fastapi import Cookie, Depends, HTTPException, status
from typing import AsyncGenerator, Annotated
from .config import settings
from app.security import decode_session_cookie
from app.service import ShortenerService, APIError
from app.dto import User
import httpx


async def _get_httpx_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    client = httpx.AsyncClient(base_url=str(settings.shortner_service), timeout=10.0)
    try:
        yield client
    finally:
        await client.aclose()


async def get_shortner_service(
    session_cookie: Annotated[str | None, Cookie(alias=settings.session_cookie)] = None,
):
    token = None
    if session_cookie:
        payload = decode_session_cookie(session_cookie)
        if payload:
            token = payload.get("token")
    async for client in _get_httpx_client():
        yield ShortenerService(client=client, token=token)


async def get_current_user(
    shortner_service: Annotated[ShortenerService, Depends(get_shortner_service)],
) -> User:
    if not shortner_service.token:
        # show the landing page or redirect or throw error.
        return None

    try:
        user: User = await shortner_service.me()
    except APIError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.detail,
        )

    return user
