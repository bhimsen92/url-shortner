from fastapi import APIRouter, Request, Depends, Response, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from app.config import templates
from typing import Annotated
from app.service import APIError, ShortenerService
from app.dependencies import get_shortner_service, get_current_user
from app.dto import UserCreate, URLItem, ShortenRequest, User, UserIn
from app.security import create_session_cookie, set_session, clear_session


auth_router = APIRouter(prefix="/auth", tags=["auth"])
web_router = APIRouter()


@auth_router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@auth_router.post("/login")
async def login_action(
    request: Request,
    response: Response,
    user_in: Annotated[UserIn, Form()],
    shortner_service: Annotated[ShortenerService, Depends(get_shortner_service)],
):
    try:
        resp = await shortner_service.login(user_in=user_in)
    except APIError as exc:
        # return to login page with error (support both normal and HTMX)
        context = {
            "request": request,
            "error": exc.detail,
        }
        return templates.TemplateResponse(
            "login.html", context, status_code=status.HTTP_401_UNAUTHORIZED
        )

    token = resp.get("access_token")
    session_cookie = create_session_cookie(
        {"token": token},
    )

    redirect_response: Response = RedirectResponse(
        url="/",
        status_code=status.HTTP_302_FOUND,
    )
    set_session(redirect_response, session_cookie)

    return redirect_response


@auth_router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@auth_router.post("/signup")
async def signup_action(
    request: Request,
    response: Response,
    user_create: Annotated[UserCreate, Form()],
    shortner_service: Annotated[ShortenerService, Depends(get_shortner_service)],
):
    try:
        resp = await shortner_service.signup(user_create=user_create)
    except APIError as exc:
        context = {
            "request": request,
            "error": exc.detail,
        }
        return templates.TemplateResponse(
            "signup.html", context, status_code=status.HTTP_400_BAD_REQUEST
        )

    token = resp.get("access_token")
    session_cookie = create_session_cookie(
        {"token": token},
    )

    redirect_response: Response = RedirectResponse(
        url="/",
        status_code=status.HTTP_302_FOUND,
    )
    set_session(redirect_response, session_cookie)

    return redirect_response


@auth_router.get("/logout")
async def logout(
    user: Annotated[User, Depends(get_current_user)],
):
    response: Response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    clear_session(response)
    return response


@web_router.get("/", response_class=HTMLResponse)
async def home(request: Request, user: Annotated[User, Depends(get_current_user)]):
    """
    If authenticated -> show index page (shorten form + results area).
    If not -> show landing page.
    """
    if user:
        return templates.TemplateResponse(
            "index.html", {"request": request, "user": user}
        )
    return templates.TemplateResponse("landing.html", {"request": request})


@web_router.post("/shorten", response_class=HTMLResponse)
async def shorten(
    request: Request,
    url_in: Annotated[ShortenRequest, Form()],
    user: Annotated[dict | None, Depends(get_current_user)],
    shortener_service: Annotated[ShortenerService, Depends(get_shortner_service)],
):
    if not user:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)

    try:
        resp: URLItem = await shortener_service.shorten(payload=url_in)
    except APIError as exc:
        detail = exc.detail
        return templates.TemplateResponse(
            "_shorten_row.html",
            {"request": request, "error": detail},
            status_code=exc.status_code,
        )

    return templates.TemplateResponse(
        "_shorten_row.html", {"request": request, "url": resp}
    )


@web_router.get("/me", response_class=HTMLResponse)
async def me(
    request: Request,
    user: Annotated[dict | None, Depends(get_current_user)],
    shortner_service: Annotated[ShortenerService, Depends(get_shortner_service)],
):
    if not user:
        return RedirectResponse(
            url="/auth/login", status_code=status.HTTP_303_SEE_OTHER
        )

    try:
        user: User = await shortner_service.me()
        summary = user.model_dump()
    except APIError:
        summary = {}

    return templates.TemplateResponse(
        "me.html",
        {
            "request": request,
            "user": user,
            "summary": summary,
        },
    )


@web_router.get("/urls", response_class=HTMLResponse)
async def list_urls(
    request: Request,
    user: Annotated[dict | None, Depends(get_current_user)],
    shortner_service: Annotated[ShortenerService, Depends(get_shortner_service)],
):
    if not user:
        return RedirectResponse(
            url="/auth/login", status_code=status.HTTP_303_SEE_OTHER
        )

    try:
        items = await shortner_service.list_urls()
    except APIError as exc:
        return templates.TemplateResponse(
            "urls.html",
            {"user": user, "request": request, "urls": [], "error": exc.detail},
            status_code=exc.status_code,
        )

    return templates.TemplateResponse(
        "urls.html",
        {
            "request": request,
            "urls": items,
            "user": user,
        },
    )
