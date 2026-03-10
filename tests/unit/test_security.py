import pytest
import jwt
from uuid_utils import uuid7

from app.core.security import create_jwt, decode_jwt, hash_password, verify_password


# ---------------------------------------------------------------------------
# Password hashing — Argon2id
# ---------------------------------------------------------------------------


def test_hash_returns_non_plaintext():
    hashed = hash_password("MyPassword123")
    assert hashed != "MyPassword123"


def test_hash_produces_argon2id_format():
    hashed = hash_password("MyPassword123")
    assert hashed.startswith("$argon2id$")


def test_verify_correct_password_returns_true():
    hashed = hash_password("MyPassword123")
    assert verify_password("MyPassword123", hashed) is True


def test_verify_wrong_password_returns_false():
    hashed = hash_password("MyPassword123")
    assert verify_password("WrongPassword", hashed) is False


def test_two_hashes_of_same_password_are_different():
    """Argon2 uses a random salt — same input produces different hashes."""
    h1 = hash_password("MyPassword123")
    h2 = hash_password("MyPassword123")
    assert h1 != h2
    # Both must still verify correctly
    assert verify_password("MyPassword123", h1) is True
    assert verify_password("MyPassword123", h2) is True


# ---------------------------------------------------------------------------
# JWT — encode / decode
# ---------------------------------------------------------------------------


_SECRET = "test-secret-key-that-is-at-least-32-bytes!!"
_OTHER_SECRET = "other-secret-key-that-is-at-least-32-bytes!"


def test_jwt_roundtrip():
    user_id = uuid7()
    token = create_jwt(user_id, _SECRET, expires_minutes=30)
    payload = decode_jwt(token, _SECRET)
    assert payload["sub"] == str(user_id)
    assert "exp" in payload
    assert "iat" in payload


def test_jwt_expired_raises():
    token = create_jwt(uuid7(), _SECRET, expires_minutes=-1)
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_jwt(token, _SECRET)


def test_jwt_wrong_secret_raises():
    token = create_jwt(uuid7(), _SECRET, expires_minutes=30)
    with pytest.raises(jwt.InvalidTokenError):
        decode_jwt(token, _OTHER_SECRET)


def test_jwt_tampered_token_raises():
    token = create_jwt(uuid7(), _SECRET, expires_minutes=30)
    tampered = token[:-4] + "xxxx"
    with pytest.raises(jwt.InvalidTokenError):
        decode_jwt(tampered, _SECRET)
