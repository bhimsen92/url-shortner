import time

import redis

from app.cache import setup_redis
from app.config import settings
from app.db import setup_postgresql
from app.dto import ClickCount
from app.service import URLClickCountService


def main():
    setup_postgresql(settings)

    redis_client: redis.Redis = setup_redis(settings)
    url_count_service = URLClickCountService()

    # setup stream group for reading purpose.
    try:
        redis_client.xgroup_create(
            settings.click_topic,
            settings.click_consumer_group,
            id="$",
            mkstream=True,
        )
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" not in str(e):
            raise

    # run the consumer forever
    while True:
        # read the records.
        records = _read_batches(redis_client, settings.batch_size)

        if records:
            records = _aggregate_records(records)
            url_count_service.increment_counts(records)

        time.sleep(1)


def _read_batches(redis_client: redis.Redis, batch_size) -> list[ClickCount]:
    return []


def _aggregate_records(records: list[ClickCount]) -> list[ClickCount]:
    pass
