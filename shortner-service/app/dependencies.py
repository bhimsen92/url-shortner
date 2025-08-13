from app.db import Session
from app.service import CounterService, URLService, UserService

counter_service = CounterService()
user_service = UserService(session=Session)
url_service = URLService(session=Session, counter_service=counter_service)
