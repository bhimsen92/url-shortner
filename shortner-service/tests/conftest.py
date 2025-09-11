import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy_utils import create_database, database_exists, drop_database

from app.config import settings
from app.main import create_app


@pytest.fixture(scope="session")
def fast_api_client() -> TestClient:
    fastapi_app = create_app()
    with TestClient(fastapi_app) as client:
        yield client


# lets setup test database for every test run.
@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    if not settings.sqlalchemy_database_uri.endswith("/test"):
        raise RuntimeError("Invalid database uri for running tests.")

    # tear down if test database already exists.
    if database_exists(settings.sqlalchemy_database_uri):
        drop_database(settings.sqlalchemy_database_uri)

    # create a fresh test database.
    create_database(settings.sqlalchemy_database_uri)

    # migrate the schema.
    _run_migrations()

    # drop the database again.
    drop_database(settings.sqlalchemy_database_uri)


def _run_migrations():
    config = Config("alembic.ini")
    command.upgrade(config=config, revision="head")
