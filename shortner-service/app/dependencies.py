from app.config import settings
from app.service import CounterService, URLService, UserService

counter_service = CounterService(
    key=settings.id_counter_key,
    batch_size=settings.id_counter_batch_size,
)
user_service = UserService()
url_service = URLService(
    counter_service=counter_service,
    hash_id_secret=settings.hash_id_counter_secret,
)


# implement session code.
