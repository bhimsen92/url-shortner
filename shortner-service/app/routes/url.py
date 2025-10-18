from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.dependencies import (
    CurrentUser,
    SessionDep,
    URLClickCountServiceDep,
    URLServiceDep,
)
from app.dto import ClickCount, URLIn, URLItem, URLOut
from app.exceptions import NotFound

urls_route = APIRouter(
    prefix="/urls",
    tags=["urls"],
)

redirect_route = APIRouter(
    prefix="",
    tags=["redirect"],
)


@urls_route.get("")
def list_urls(
    request: Request, user: CurrentUser, url_service: URLServiceDep
) -> list[URLItem]:
    url_items = [
        URLItem(
            short_url=f"{settings.base_url}{url.short_url}",
            original_url=url.original_url,
            expires_at=url.expires_at,
        )
        for url in url_service.list_urls(user=user)
    ]
    return url_items


@urls_route.post("/shorten")
def shorten_url(
    url_in: URLIn,
    session: SessionDep,
    user: CurrentUser,
    url_service: URLServiceDep,
) -> URLOut:
    try:
        short_url = url_service.shorten_url(url_data=url_in, user=user)
        return URLOut(short_url=f"{settings.base_url}{short_url}")
    except IntegrityError:
        msg = "Unable to create short-url, please try again later."
        if url_in.alias:
            msg = f"A short url with alias: {url_in.alias} already exist. Please try with another alias."

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=msg,
        )


@urls_route.get("/stats/{short_url}")
def click_stats(
    short_url: str,
    session: SessionDep,
    user: CurrentUser,
    url_click_count_service: URLClickCountServiceDep,
    limit: int = Query(default=50, ge=1, le=100, description="Page size"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
) -> list[ClickCount]:
    return url_click_count_service.get_stats(
        short_url=short_url,
        offset=offset,
        limit=limit,
    )


@redirect_route.get("/{short_url}")
def redirect_short_url(
    request: Request,
    short_url: str,
    session: SessionDep,
    url_service: URLServiceDep,
):
    try:
        original_url = url_service.un_shorten(short_url=short_url)

        # add short url and ip to stream.
        url_service.record_click(short_url, request.client.host)

        return RedirectResponse(url=original_url, status_code=302)
    except NotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
