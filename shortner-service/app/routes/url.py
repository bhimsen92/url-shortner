from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import IntegrityError

from app.dependencies import CurrentUser, SessionDep, URLServiceDep
from app.dto import URLIn, URLOut
from app.exceptions import NotFound

urls_route = APIRouter(
    prefix="/urls",
    tags=["urls"],
)

redirect_route = APIRouter(
    prefix="",
    tags=["redirect"],
)


@urls_route.post("/shorten")
def shorten_url(
    url_in: URLIn,
    session: SessionDep,
    request: Request,
    user: CurrentUser,
    url_service: URLServiceDep,
) -> URLOut:
    try:
        short_url = url_service.shorten_url(url_data=url_in, user=user)
        session.commit()
        return URLOut(short_url=f"{request.base_url}{short_url}")
    except IntegrityError:
        msg = "Unable to create short-url, please try again later."
        if url_in.alias:
            msg = f"A short url with alias: {url_in.alias} already exist. Please try with another alias."

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=msg,
        )


@redirect_route.get("/{short_url}")
def redirect_short_url(short_url: str, url_service: URLServiceDep):
    try:
        original_url = url_service.un_shorten(short_url=short_url)
        return RedirectResponse(url=original_url, status_code=302)
    except NotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
