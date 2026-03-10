from datetime import timedelta
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError

from app.core.utils import utcnow

# module-level singleton — PasswordHasher is thread-safe and cheap to reuse;
# creating it once avoids re-parsing Argon2 tuning parameters on every call
_ph = PasswordHasher()


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        # argon2 API signature is verify(hash, plain) — not (plain, hash)
        return _ph.verify(hashed, password)
    except VerifyMismatchError:
        # password does not match the stored hash
        return False
    except VerificationError:
        # hash is malformed or uses parameters the library can't handle
        return False


def create_jwt(user_id: UUID, secret_key: str, expires_minutes: int = 30) -> str:
    now = utcnow()
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
    }
    return jwt.encode(payload, secret_key, algorithm="HS256")


def decode_jwt(token: str, secret_key: str) -> dict:
    """Decode and verify a JWT. Raises jwt.ExpiredSignatureError or jwt.InvalidTokenError."""
    return jwt.decode(token, secret_key, algorithms=["HS256"])
