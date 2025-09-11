import pytest

from app.config import settings


@pytest.fixture(scope="module")
def user_token(fast_api_client):
    # get the user token.
    response = fast_api_client.post(
        f"{settings.API_V1}/users/access-token",
        json={
            "username": "test",
            "password": "test",
        },
    )

    assert response.status_code == 200

    token = response.json()["token"]
    yield token


def test_user_creation_endpoint(fast_api_client):
    response = fast_api_client.post(
        f"{settings.API_V1}/users",
        json={
            "username": "test",
            "password": "test",
            "display_name": "Test",
        },
    )
    assert response.status_code == 200
    assert response.json()["token"] is not None

    token = response.json()["token"]

    # validate that user is created.
    response = fast_api_client.get(
        f"{settings.API_V1}/users/me", headers={{"Authorization": f"Bearer {token}"}}
    )

    assert response.status_code == 200
    assert response.json() == {
        "username": "test",
        "display_name": "Test",
        "is_active": True,
    }


def test_redirect_short_url(fast_api_client, user_token):
    # shorten the url.
    response = fast_api_client.post(
        f"{settings.API_V1}/urls/shorten",
        json={
            "original_url": "http://localhost:8080/testing-long-url-very-long",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )
    short_url = response.json()["short_url"]
    short_url_code = short_url.split("/")[-1]
    assert len(short_url_code) <= 6

    # check redirect.
    response = fast_api_client.get(short_url)
    assert (
        response.headers["Location"]
        == "http://localhost:8080/testing-long-url-very-long"
    )


def test_redirect_short_url_with_alias(fast_api_client, user_token):
    # shorten the url.
    response = fast_api_client.post(
        f"{settings.API_V1}/urls/shorten",
        json={
            "original_url": "http://localhost:8080/testing-long-url-very-long",
            "alias": "test",
        },
        headers={"Authorization": f"Bearer {user_token}"},
    )

    short_url = response.json()["short_url"]
    assert short_url.split("/")[-1] == "test"

    # check redirect.
    response = fast_api_client.get(short_url)
    assert (
        response.headers["Location"]
        == "http://localhost:8080/testing-long-url-very-long"
    )


def test_list_shorten_urls(fast_api_client, user_token):
    response = fast_api_client.get(
        f"{settings.API_V1}/urls",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    assert len(response.json()) >= 1


# error scenarios.
def test_shorten_url_with_same_alias_error(fast_api_client, user_token):
    for alias, status_code in [("test-1", 200), ("test-1", 409)]:
        response = fast_api_client.post(
            f"{settings.API_V1}/urls/shorten",
            json={
                "original_url": "http://localhost:8080/testing-long-url-very-long",
                "alias": f"{alias}",
            },
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == status_code


def test_redirect_url_invalid_short_url_error(fast_api_client):
    response = fast_api_client.get(
        f"{settings.API_V1}/random-code",
    )
    assert response.status_code == 404


def test_invalid_user_login_error(fast_api_client):
    for username, password, status_code in [
        ("test", "test-1", 401),
        ("test-2", "test-2", 401),
    ]:
        response = fast_api_client.post(
            f"{settings.API_V1}/users/access-token",
            json={
                "username": username,
                "password": password,
            },
        )

        assert response.status_code == status_code


def test_same_user_creation_error(fast_api_client):
    response = fast_api_client.post(
        f"{settings.API_V1}/users",
        json={
            "username": "test",
            "password": "test",
            "display_name": "Test",
        },
    )

    assert response.status_code == 409
