import logging
import time
import uuid
from collections import defaultdict

import redis

from app.cache import setup_redis
from app.config import settings
from app.db import SessionContext, current_ctx, setup_postgresql
from app.dto import ClickCount, ClickStreamMessage
from app.log import setup_logging
from app.service import URLClickCountService

LOG = logging.getLogger()


def main():
    setup_logging()

    LOG.info("setting up postgresql client.")
    setup_postgresql(settings)

    LOG.info("setting up redis client.")
    redis_client: redis.Redis = setup_redis(settings)
    url_count_service = URLClickCountService(context=current_ctx)

    # consumer group name
    consumer_name = f"{settings.click_analytics_consumer_group}-{uuid.uuid4()}"
    LOG.info(f"consumer name: {consumer_name}")

    # setup stream group for reading purpose.
    try:
        redis_client.xgroup_create(
            settings.click_analytics_topic,
            settings.click_analytics_consumer_group,
            id="$",
            mkstream=True,
        )
        LOG.info(f"group: {settings.click_analytics_consumer_group} created.")
    except redis.exceptions.ResponseError as e:
        if "BUSYGROUP" not in str(e):
            raise
        LOG.info(f"group: {settings.click_analytics_consumer_group} already exists.")

    # run the consumer forever
    LOG.info("Start reading message...")
    while True:
        # read the records.
        records = _read_batches(redis_client, consumer_name)

        if not records:
            LOG.debug("No messages found in the current read, sleeping for 10 seconds.")
            time.sleep(10)
            continue

        agg_records = _aggregate_records(records)
        with SessionContext(with_transaction=True):
            url_count_service.increment_counts(agg_records)

        redis_client.xack(
            settings.click_analytics_topic,
            settings.click_analytics_consumer_group,
            *[record.message_id for record in records],
        )
        LOG.info(f"Ingested {len(records)} messages.")

        LOG.info("sleeping for 5 second.")
        time.sleep(5)


def _read_batches(
    redis_client: redis.Redis, consumer_name: str
) -> list[ClickStreamMessage]:
    stream_messages = redis_client.xreadgroup(
        groupname=settings.click_analytics_consumer_group,
        consumername=consumer_name,
        streams={
            settings.click_analytics_topic: ">",
        },
        count=settings.click_analytics_batch_count,
        block=1000,
    )

    if not stream_messages:
        return []

    return_value = []
    for stream_name, messages in stream_messages:
        for msg_id, message in messages:
            return_value.append(
                ClickStreamMessage(message_id=msg_id, **message),
            )

    return return_value


def _aggregate_records(records: list[ClickStreamMessage]) -> list[ClickCount]:
    counts = defaultdict(int)

    for record in records:
        country_code = _ip_to_country(record.request_ip)
        counts[(record.short_url, country_code)] += 1

    return_value = []
    for key, counts in counts.items():
        return_value.append(
            ClickCount(short_url=key[0], country_code=key[1], counts=counts),
        )

    return return_value


def _ip_to_country(ip: str) -> str:
    return "TBD"


if __name__ == "__main__":
    main()
