import pytest
from app.core.utils import uuid7

from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictException, NotAuthenticatedException
from app.core.security import hash_password
from app.models.user import User
from app.schemas.auth import LoginRequest, UserCreate
from app.services.auth import AuthService

_SECRET = "a-very-long-secret-key-that-is-32bytes!"


async def test_register_creates_user(mock_user_repo):
    mock_user_repo.get_by_email.return_value = None
    mock_user_repo.create.return_value = User(
        id=uuid7(), email="a@b.com", full_name="A B", password="hashed"
    )

    service = AuthService(mock_user_repo)
    user = await service.register(
        UserCreate(email="a@b.com", password="Strong123!", full_name="A B")
    )

    assert user.email == "a@b.com"
    mock_user_repo.create.assert_called_once()


async def test_register_duplicate_email_raises(mock_user_repo):
    mock_user_repo.create.side_effect = IntegrityError(
        statement="INSERT", params={}, orig=Exception("duplicate key")
    )

    service = AuthService(mock_user_repo)
    with pytest.raises(ConflictException):
        await service.register(
            UserCreate(email="a@b.com", password="Strong123!", full_name="A B")
        )


async def test_login_success_returns_token(mock_user_repo):
    hashed = hash_password("correct-password")
    mock_user_repo.get_by_email.return_value = User(
        id=uuid7(), email="a@b.com", full_name="A B", password=hashed
    )

    service = AuthService(mock_user_repo)
    token = await service.login(
        LoginRequest(email="a@b.com", password="correct-password"),
        secret_key=_SECRET,
        expires_minutes=30,
    )

    assert isinstance(token, str)
    assert len(token) > 0


async def test_login_user_not_found_raises(mock_user_repo):
    mock_user_repo.get_by_email.return_value = None

    service = AuthService(mock_user_repo)
    with pytest.raises(NotAuthenticatedException):
        await service.login(
            LoginRequest(email="notfound@example.com", password="anypassword"),
            secret_key=_SECRET,
            expires_minutes=30,
        )


async def test_login_wrong_password_raises(mock_user_repo):
    hashed = hash_password("correct-password")
    mock_user_repo.get_by_email.return_value = User(
        id=uuid7(), email="a@b.com", full_name="A B", password=hashed
    )

    service = AuthService(mock_user_repo)
    with pytest.raises(NotAuthenticatedException):
        await service.login(
            LoginRequest(email="a@b.com", password="wrong-password"),
            secret_key=_SECRET,
            expires_minutes=30,
        )


def test_password_validation_success():
    # Should not raise any validation errors
    user = UserCreate(email="test@test.com", password="Strong123!", full_name="Test")
    assert user.password == "Strong123!"

def test_password_validation_no_uppercase_raises():
    from pydantic import ValidationError
    with pytest.raises(ValidationError, match="uppercase"):
        UserCreate(email="test@test.com", password="weak123!", full_name="Test")

def test_password_validation_no_number_raises():
    from pydantic import ValidationError
    with pytest.raises(ValidationError, match="number"):
        UserCreate(email="test@test.com", password="Weakpassword!", full_name="Test")

def test_password_validation_no_special_char_raises():
    from pydantic import ValidationError
    with pytest.raises(ValidationError, match="special character"):
        UserCreate(email="test@test.com", password="WeakPassword123", full_name="Test")

def test_password_validation_too_short_raises():
    from pydantic import ValidationError
    with pytest.raises(ValidationError, match="String should have at least 8 characters"):
        UserCreate(email="test@test.com", password="Wk1!", full_name="Test")
