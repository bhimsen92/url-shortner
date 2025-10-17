import threading
import uuid

from hashids import Hashids
from sqlmodel import select, update

from app.cache import RedisCache
from app.db import CurrentSessionContext
from app.dto import ClickCount, Token, URLIn, UserCreate, UserLogin
from app.exceptions import NotFound
from app.models import URL, IDCounter, User
from app.security import hash_password, validate_password


class UserService:
    def __init__(self, *, context: CurrentSessionContext):
        self.ctx = context

    def create_user(self, *, user_data: UserCreate) -> User:
        user = User(
            username=user_data.username,
            display_name=user_data.display_name,
            hashed_password=hash_password(user_data.password),
        )
        self.ctx.session.add(user)

        # flush is done to quickly identify any integrity error.
        self.ctx.session.flush()

        return user

    def create_token(self, *, user_data: UserLogin) -> Token:
        user = self.ctx.session.exec(
            select(User).where(
                User.username == user_data.username,
            ),
        ).one_or_none()

        if user and validate_password(user_data.password, user.hashed_password):
            return Token(access_token=user.token())
        else:
            raise NotFound("Invalid username or password.")

    def get_user(self, *, user_id: uuid.UUID) -> User:
        user = self.ctx.session.exec(
            select(User).where(User.id == user_id)
        ).one_or_none()
        if user:
            return user
        else:
            raise NotFound(f"User with id: {user_id} not found.")


class CounterService:
    def __init__(
        self, *, key: str, batch_size: int = 1000, context: CurrentSessionContext
    ):
        self.key: str = key
        self.batch_size: int = batch_size
        self.ctx = context

        self._lock = threading.RLock()
        self._max_id = -1
        self._next_id = None

    def get_next_id(self) -> int:
        with self._lock:
            if self._next_id is None or self._next_id > self._max_id:
                self._refill()

            current_id = self._next_id
            self._next_id += 1

            return current_id

    def _refill(self):
        stmt = (
            update(IDCounter)
            .where(IDCounter.key == self.key)
            .values(next_id=IDCounter.next_id + self.batch_size)
            .returning(IDCounter.next_id)
        )
        result = self.ctx.session.exec(stmt).one_or_none()

        new_next_id = result.next_id
        start_id = new_next_id - self.batch_size

        self._next_id = start_id
        self._max_id = new_next_id - 1


class URLService:
    def __init__(
        self,
        *,
        counter_service: CounterService,
        hash_id_secret: str,
        min_hash_len: int = 6,
        context: CurrentSessionContext,
        redis_cache: RedisCache,
        clicks_topic: str,
    ):
        self.counter_service = counter_service
        self.hash_id_secret = hash_id_secret
        self.min_hash_len = min_hash_len
        self.ctx = context

        # for tracking redirect counts.
        self.clicks_topic = clicks_topic
        self.cache: RedisCache = redis_cache

        self.hashids = Hashids(
            salt=self.hash_id_secret,
            min_length=self.min_hash_len,
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        )

    def list_urls(self, *, user: User) -> list[URL]:
        urls = self.ctx.session.exec(select(URL).where(URL.created_by == user.id))
        return urls

    def shorten_url(self, *, url_data: URLIn, user: User) -> str:
        if url_data.alias:
            short_url = url_data.alias
        else:
            short_id = self.counter_service.get_next_id()
            short_url = self.hashids.encode(short_id)

        url = URL(
            original_url=url_data.original_url,
            short_url=short_url,
            created_by=user.id,
            expires_at=url_data.expires_in,
        )
        self.ctx.session.add(url)

        # flush is done to quickly identify any integrity error.
        self.ctx.session.flush()

        return short_url

    def un_shorten(self, short_url: str) -> str:
        # if the short code is cached, return it from there.
        if original_url := self.cache.get(key=short_url):
            return original_url

        urls = self.ctx.session.exec(select(URL).where(URL.short_url == short_url))

        try:
            (url,) = urls

            # cache the mapping for future use.
            self.cache.set(key=short_url, value=url.original_url)

            return url.original_url
        except ValueError:
            raise NotFound(f"Invalid short-url: {short_url}")

    def record_click(self, short_url, request_ip: str):
        self.cache.produce_to_topic(
            self.clicks_topic,
            message={
                "short_url": short_url,
                "request_ip": request_ip,
            },
        )


class URLClickCountService:
    def increment_counts(self, records: list[ClickCount]) -> None: ...
