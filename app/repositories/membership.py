from uuid import UUID

from sqlalchemy import asc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.membership import Membership
from app.models.user import User


class MembershipRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, membership: Membership) -> Membership:
        self.session.add(membership)
        await self.session.flush()
        return membership

    async def get(self, user_id: UUID, org_id: UUID) -> Membership | None:
        result = await self.session.execute(
            select(Membership).where(
                Membership.user_id == user_id,
                Membership.org_id == org_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_user_and_membership(
        self, email: str, org_id: UUID
    ) -> tuple[User | None, Membership | None]:
        """Single query: fetch the user by email + their membership in org_id (if any)."""
        result = await self.session.execute(
            select(User, Membership)
            .outerjoin(
                Membership,
                (Membership.user_id == User.id) & (Membership.org_id == org_id),
            )
            .where(User.email == email)
        )
        row = result.one_or_none()
        if row is None:
            return None, None
        return row.User, row.Membership

    async def get_users_in_org(
        self, org_id: UUID, limit: int, offset: int
    ) -> tuple[list, int]:
        base = (
            select(User, Membership.role)
            .join(Membership, Membership.user_id == User.id)
            .where(Membership.org_id == org_id)
        )
        count_result = await self.session.execute(
            select(func.count()).select_from(base.subquery())
        )
        total = count_result.scalar() or 0
        result = await self.session.execute(
            base.order_by(asc(Membership.created_at)).offset(offset).limit(limit)
        )
        return list(result.all()), total
