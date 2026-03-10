from uuid import UUID

from app.core.exceptions import ConflictException, NotFoundException
from app.models.audit_log import AuditLog
from app.models.membership import Membership, Role
from app.models.organization import Organization
from app.repositories.audit_log import AuditLogRepository
from app.repositories.membership import MembershipRepository
from app.repositories.organization import OrganizationRepository
from app.repositories.user import UserRepository


class OrgService:
    def __init__(
        self,
        org_repo: OrganizationRepository,
        membership_repo: MembershipRepository,
        user_repo: UserRepository,
        audit_repo: AuditLogRepository,
    ) -> None:
        self.org_repo = org_repo
        self.membership_repo = membership_repo
        self.user_repo = user_repo
        self.audit_repo = audit_repo

    async def create_organization(self, name: str, creator_id: UUID) -> Organization:
        org = Organization(name=name)
        org = await self.org_repo.create(org)
        await self.membership_repo.create(
            Membership(user_id=creator_id, org_id=org.id, role=Role.ADMIN)
        )
        await self.audit_repo.create(
            AuditLog(
                org_id=org.id,
                user_id=creator_id,
                action="org_created",
                entity_type="organization",
                entity_id=org.id,
                details={"org_name": name},
            )
        )
        return org

    async def invite_user(
        self, org_id: UUID, email: str, role: str, inviter_id: UUID
    ) -> Membership:
        user, existing = await self.membership_repo.get_user_and_membership(email, org_id)
        if not user:
            raise NotFoundException("User not found")
        if existing:
            raise ConflictException("User already in organization")
        membership = Membership(user_id=user.id, org_id=org_id, role=Role(role))
        membership = await self.membership_repo.create(membership)
        await self.audit_repo.create(
            AuditLog(
                org_id=org_id,
                user_id=inviter_id,
                action="user_invited",
                entity_type="membership",
                entity_id=user.id,
                details={"invited_email": email, "role": role},
            )
        )
        return membership

    async def list_users(
        self, org_id: UUID, limit: int, offset: int
    ) -> tuple[list, int]:
        return await self.membership_repo.get_users_in_org(org_id, limit, offset)

    async def search_users(
        self, org_id: UUID, query: str, limit: int, offset: int
    ) -> tuple[list, int]:
        return await self.user_repo.search_in_org(org_id, query, limit, offset)
