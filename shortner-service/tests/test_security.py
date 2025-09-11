from app.security import decode_jwt, encode_jwt, hash_password, validate_password


def test_validate_hash_password():
    assert validate_password("test", hash_password("test"))
    assert validate_password("tests", hash_password("test")) is False


def test_decode_encode_jwt():
    payload = {
        "id": 1,
        "username": "test",
    }
    jwt_string = encode_jwt(payload)

    decoded_payload = decode_jwt(jwt_string)
    assert decoded_payload == payload
