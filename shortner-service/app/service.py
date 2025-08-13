import uuid

from sqlalchemy.orm import scoped_session

from app.dto import Token, URLIn, UserLogin, UserSignUp
from app.models import User


class UserService:
    def __init__(self, session: scoped_session):
        self.session = session

    def create_user(self, user_data: UserSignUp) -> User:
        pass

    def create_token(self, user_data: UserLogin) -> Token:
        pass

    def get_user(self, user_id: uuid.UUID) -> User:
        pass


class CounterService:
    def get_next_id(self) -> int:
        pass


class URLService:
    def __init__(self, session: scoped_session, counter_service: CounterService):
        self.session = session
        self.counter_service = counter_service

    def shorten_url(self, url_data: URLIn) -> str:
        pass

    def un_shorten(self, short_url: str) -> str:
        pass
