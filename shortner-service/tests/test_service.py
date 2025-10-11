from concurrent.futures import ThreadPoolExecutor

from app.config import settings
from app.db import SessionContext, current_ctx
from app.service import CounterService


def test_get_next_id_conflict_free():
    batch_size = 10
    counter_service = CounterService(
        key=settings.id_counter_key,
        batch_size=batch_size,
        context=current_ctx,
    )

    num_threads = 10
    ids_per_thread = 1000

    def worker():
        return_values = []
        for _ in range(ids_per_thread):
            # we need to create session for each call, otherwise it will end up
            # in deadlock. Because each session won't commit until it has exhausted
            # the whole ids_per_thread. Since batch_size is just 10, two threads
            # would end up update the same row and hence getting stuck forever.
            with SessionContext(atomic=True):
                return_values.append(counter_service.get_next_id())

        return return_values

    with ThreadPoolExecutor(max_workers=num_threads) as pool:
        futures = [
            pool.submit(
                worker,
            )
            for _ in range(num_threads)
        ]

    all_ids = []
    for future in futures:
        all_ids.extend(future.result())

    total = num_threads * ids_per_thread
    assert len(all_ids) == total
    assert len(set(all_ids)) == total
