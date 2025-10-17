from contextlib import asynccontextmanager

import redis
from fastapi import FastAPI

from app.cache import RedisCache, close_redis_connections, setup_redis
from app.config import settings
from app.db import close_db_connections, current_ctx, setup_postgresql
from app.routes.url import redirect_route, urls_route
from app.routes.user import route as user_routes
from app.service import CounterService, URLService, UserService


@asynccontextmanager
def app_setup(app: FastAPI):
    # setup postgresql database connection.
    setup_postgresql(settings)

    # setup redis client.
    redis_client: redis.Redis = setup_redis(settings)

    # setup services.
    counter_service = CounterService(
        key=settings.id_counter_key,
        batch_size=settings.id_counter_batch_size,
        context=current_ctx,
    )
    user_service = UserService(
        context=current_ctx,
    )
    url_service = URLService(
        counter_service=counter_service,
        hash_id_secret=settings.hash_id_counter_secret,
        context=current_ctx,
        redis_cache=RedisCache(client=redis_client),
        clicks_topic=settings.click_analytics_topic,
    )

    app.state.countr_service = counter_service
    app.state.user_service = user_service
    app.state.url_service = url_service

    try:
        yield
    finally:
        close_db_connections()
        close_redis_connections()


def create_app() -> FastAPI:
    app = FastAPI()

    app.include_router(user_routes, prefix=settings.API_V1)
    app.include_router(urls_route, prefix=settings.API_V1)
    app.include_router(redirect_route)

    return app
