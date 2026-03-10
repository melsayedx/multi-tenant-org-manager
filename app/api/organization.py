from uuid import UUID

from fastapi import APIRouter, Depends, Query

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, require_admin
from app.infrastructure.database import get_db
from app.models.membership import Membership
from app.models.user import User
from app.repositories.audit_log import AuditLogRepository
from app.repositories.membership import MembershipRepository
from app.repositories.organization import OrganizationRepository
from app.repositories.user import UserRepository
from app.schemas.organization import (
    InviteUser,
    OrgCreate,
    OrgResponse,
    PaginatedUsers,
    UserInOrg,
)
from app.services.organization import OrgService

router = APIRouter(tags=["organizations"])


def _org_service(db: AsyncSession) -> OrgService:
    return OrgService(
        OrganizationRepository(db),
        MembershipRepository(db),
        UserRepository(db),
        AuditLogRepository(db),
    )


@router.post("/organization", response_model=OrgResponse, status_code=201)
async def create_organization(
    data: OrgCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org = await _org_service(db).create_organization(data.org_name, user.id)
    return OrgResponse(org_id=org.id)


@router.post("/organization/{org_id}/user", status_code=201)
async def invite_user(
    org_id: UUID,
    data: InviteUser,
    _: Membership = Depends(require_admin),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _org_service(db).invite_user(org_id, data.email, data.role, user.id)
    return {"message": "User invited successfully"}


@router.get("/organizations/{org_id}/users", response_model=PaginatedUsers)
async def list_users(
    org_id: UUID,
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    _: Membership = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    users, total = await _org_service(db).list_users(org_id, limit, offset)
    return PaginatedUsers(
        users=[
            UserInOrg(id=u.id, email=u.email, full_name=u.full_name, role=r.value)
            for u, r in users
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/organizations/{org_id}/users/search", response_model=list[UserInOrg])
async def search_users(
    org_id: UUID,
    q: str = Query(min_length=1),
    _: Membership = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    users = await _org_service(db).search_users(org_id, q)
    return [
        UserInOrg(id=u.id, email=u.email, full_name=u.full_name, role=r.value)
        for u, r in users
    ]
