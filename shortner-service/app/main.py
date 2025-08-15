from fastapi import FastAPI

from app.config import settings
from app.routes.url import redirect_route, urls_route
from app.routes.user import route as user_routes


def create_app() -> FastAPI:
    app = FastAPI()

    app.include_router(user_routes, prefix=settings.API_V1)
    app.include_router(urls_route, prefix=settings.API_V1)
    app.include_router(redirect_route)

    return app
