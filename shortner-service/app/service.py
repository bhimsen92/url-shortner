import threading
import uuid

from hashids import Hashids
from sqlmodel import Session, select, update

from app.dto import Token, URLIn, UserCreate, UserLogin
from app.exceptions import NotFound
from app.models import URL, IDCounter, User
from app.security import hash_password


class UserService:
    def create_user(self, *, user_data: UserCreate, session: Session) -> User:
        user = User(
            username=user_data.username,
            display_name=user_data.display_name,
            hashed_password=hash_password(user_data.password),
        )
        session.add(user)

        return user

    def create_token(self, *, user_data: UserLogin, session: Session) -> Token:
        user = session.exec(
            select(User).where(
                User.username == user_data.username,
                User.hashed_password == hash_password(user_data.password),
            ),
        ).one_or_none()

        if user:
            return Token(access_token=user.token())
        else:
            raise NotFound(f"User with username: {user_data.username} not found.")

    def get_user(self, *, user_id: uuid.UUID, session: Session) -> User:
        user = session.exec(select(User).where(User.id == user_id)).one_or_none()
        if user:
            return user
        else:
            raise NotFound(f"User with id: {user_id} not found.")


class CounterService:
    def __init__(
        self,
        *,
        key: str,
        batch_size: int = 1000,
    ):
        self.key: str = key
        self.batch_size: int = batch_size

        self._lock = threading.RLock()
        self._max_id = -1
        self._next_id = None

    def get_next_id(self, *, session: Session) -> int:
        with self._lock:
            if self._next_id is None or self._next_id > self._max_id:
                self._refill(session=session)

            current_id = self._next_id
            self._next_id += 1

            return current_id

    def _refill(self, *, session: Session):
        stmt = (
            update(IDCounter)
            .where(IDCounter.key == self.key)
            .values(next_id=IDCounter.next_id + self.batch_size)
            .returning(IDCounter.next_id)
        )
        result = session.exec(stmt).one_or_none()

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
    ):
        self.counter_service = counter_service
        self.hash_id_secret = hash_id_secret
        self.min_hash_len = min_hash_len

        self.hashids = Hashids(
            salt=self.hash_id_secret,
            min_length=self.min_hash_len,
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        )

    def shorten_url(self, *, url_data: URLIn, user: User, session: Session) -> str:
        if url_data.alias:
            short_url = url_data.alias
        else:
            short_id = self.counter_service.get_next_id(session=session)
            short_url = self.hashids.encode(short_id)

        url = URL(
            original_url=url_data.original_url,
            short_url=short_url,
            created_by=user.id,
            expires_at=url_data.expires_in,
        )
        session.add(url)

        return short_url

    def un_shorten(self, short_url: str, session: Session) -> str:
        urls = session.exec(select(URL).where(URL.short_url == short_url))

        try:
            (url,) = urls
            return url.original_url
        except ValueError:
            raise NotFound(f"Invalid short-url: {short_url}")
