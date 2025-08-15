# app/api_client.py
from typing import Optional, Dict, Any, List
import httpx
from app.dto import UserIn, ShortenRequest, UserCreate, User, URLItem


class APIError(Exception):
    def __init__(self, status_code: int, detail: Any):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"APIError {status_code}: {detail}")


class ShortenerService:
    def __init__(self, client: httpx.AsyncClient, token: Optional[str] = None):
        self.client = client
        self.token = token

    def _headers(self) -> Dict[str, str]:
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    async def login(self, user_in: UserIn) -> Dict[str, Any]:
        resp = await self.client.post(
            "/api/v1/users/access-token",
            json=user_in.model_dump(),
        )
        if resp.status_code != 200:
            raise APIError(resp.status_code, resp.json())
        return resp.json()

    async def signup(self, user_create: UserCreate) -> Dict[str, Any]:
        resp = await self.client.post(
            "/api/v1/users/signup", json=user_create.model_dump()
        )
        if resp.status_code not in (200, 201):
            raise APIError(resp.status_code, resp.json())
        return resp.json()

    async def me(self) -> User:
        resp = await self.client.get("/api/v1/users/me", headers=self._headers())
        if resp.status_code != 200:
            raise APIError(resp.status_code, resp.json())
        return User(**resp.json())

    async def list_urls(self) -> List[URLItem]:
        resp = await self.client.get("/api/v1/urls", headers=self._headers())
        if resp.status_code != 200:
            raise APIError(resp.status_code, resp.json())
        return [URLItem(**it) for it in resp.json()]

    async def shorten(self, payload: ShortenRequest) -> URLItem:
        resp = await self.client.post(
            "/api/v1/urls/shorten",
            json=payload.model_dump(exclude_none=True),
            headers=self._headers(),
        )
        if resp.status_code not in (200, 201):
            raise APIError(resp.status_code, resp.json())
        return URLItem(**{**payload.model_dump(), **resp.json()})
