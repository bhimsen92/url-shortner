from concurrent.futures import ThreadPoolExecutor

from app.config import settings
from app.db import current_ctx
from app.service import CounterService


def test_get_next_id_conflict_free():
    batch_size = 10
    counter_service = CounterService(
        key=settings.id_counter_key,
        batch_size=batch_size,
        context=current_ctx,
    )

    num_threads = 5
    ids_per_thread = 100

    def worker():
        return [counter_service.get_next_id() for _ in range(ids_per_thread)]

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
