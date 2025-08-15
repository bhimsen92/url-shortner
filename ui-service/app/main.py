from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.routes import web_router, auth_router


def create_app():
    app = FastAPI()

    # Mount static if you have local assets
    app.mount("/static", StaticFiles(directory="static"), name="static")

    app.include_router(auth_router)
    app.include_router(web_router)

    return app
