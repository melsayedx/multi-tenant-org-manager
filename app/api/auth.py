from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.infrastructure.database import get_db
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, TokenResponse, UserCreate, UserResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    service = AuthService(UserRepository(db))
    user = await service.register(data)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    service = AuthService(UserRepository(db))
    token = await service.login(data, settings.jwt_secret_key, settings.jwt_expiration_minutes)
    return TokenResponse(access_token=token)

@router.post("/token", response_model=TokenResponse, include_in_schema=False)
async def token(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """OAuth2 form-based login — used by OpenAPI UI's Authorize button."""
    service = AuthService(UserRepository(db))
    access_token = await service.login(
        LoginRequest(email=form.username, password=form.password),
        settings.jwt_secret_key,
        settings.jwt_expiration_minutes,
    )
    return TokenResponse(access_token=access_token)
