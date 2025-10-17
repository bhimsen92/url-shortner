from typing import Optional

import redis

from app.config import Settings

_redis_client: redis.Redis = None


class RedisCache:
    def __init__(self, client: redis.Redis):
        self._client = client

    def get(self, key: str) -> Optional[str]:
        value: str = self._client.get(key)
        return value

    def set(self, key: str, value: str, expire_seconds: Optional[int] = None) -> None:
        if expire_seconds:
            self._client.set(key, value, ex=expire_seconds)
        else:
            self._client.set(key, value)

    def produce_to_topic(self, topic: str, message: dict) -> None:
        self._client.xadd(name=topic, fields=message)


def setup_redis(settings: Settings) -> redis.Redis:
    global _redis_client

    _redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


def close_redis_connections():
    _redis_client.close()


def get_redis_client():
    """Helper method to return redis client object"""
    return _redis_client
