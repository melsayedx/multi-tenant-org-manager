from sqlalchemy.exc import IntegrityError

from app.core.exceptions import ConflictException, NotAuthenticatedException
from app.core.security import create_jwt, hash_password, verify_password
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, UserCreate


class AuthService:
    def __init__(self, user_repo: UserRepository) -> None:
        self.user_repo = user_repo

    async def register(self, data: UserCreate) -> User:
        user = User(
            email=data.email,
            full_name=data.full_name,
            password=hash_password(data.password),
        )

        try:
            return await self.user_repo.create(user)
        except IntegrityError as err:
            raise ConflictException("Email already registered") from err

    async def login(
        self, data: LoginRequest, secret_key: str, expires_minutes: int
    ) -> str:
        user = await self.user_repo.get_by_email(data.email)
        if not user or not verify_password(data.password, user.password.strip()):
            raise NotAuthenticatedException("Invalid email or password")
        return create_jwt(user.id, secret_key, expires_minutes)
