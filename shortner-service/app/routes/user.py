from fastapi import APIRouter

route = APIRouter(
    prefix="/users",
)


@route.post("/")
def create_user():
    pass


@route.get("/<id>")
def get_user():
    pass


@route.get("/access-token")
def get_token():
    pass
