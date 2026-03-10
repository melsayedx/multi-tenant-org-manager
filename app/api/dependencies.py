from uuid import UUID

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import ForbiddenException, NotAuthenticatedException
from app.core.security import decode_jwt
from app.infrastructure.database import get_db
from app.models.membership import Membership, Role
from app.models.user import User
from app.repositories.membership import MembershipRepository
from app.repositories.user import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = decode_jwt(token, settings.jwt_secret_key)
        user_id = UUID(payload["sub"])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, KeyError, ValueError):
        raise NotAuthenticatedException()
    user = await UserRepository(db).get_by_id(user_id)
    if not user:
        raise NotAuthenticatedException()
    return user


async def require_membership(
    org_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Membership:
    membership = await MembershipRepository(db).get(user.id, org_id)
    if not membership:
        raise ForbiddenException("Not a member of this organization")
    return membership


async def require_admin(
    org_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Membership:
    membership = await MembershipRepository(db).get(user.id, org_id)
    if not membership or membership.role != Role.ADMIN:
        raise ForbiddenException("Admin access required")
    return membership
