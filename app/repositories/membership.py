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
        return await self.session.get(Membership, (user_id, org_id))

    async def get_user_and_membership(
        self, email: str, org_id: UUID
    ) -> tuple[User | None, Membership | None]:
        """Single query: fetch the user by email + their membership in org_id (if any)."""
        row = (
            await self.session.execute(
                select(User, Membership)
                .outerjoin(
                    Membership,
                    (Membership.user_id == User.id) & (Membership.org_id == org_id),
                )
                .where(User.email == email)
            )
        ).first()

        return row._tuple() if row else (None, None)

    async def get_users_in_org(self, org_id: UUID, limit: int, offset: int) -> tuple[list, int]:
        base = (
            select(User, Membership.role, func.count().over().label("total"))
            .join(Membership, Membership.user_id == User.id)
            .where(Membership.org_id == org_id)
            .order_by(asc(Membership.created_at))
            .offset(offset)
            .limit(limit)
        )
        rows = (await self.session.execute(base)).all()
        if not rows:
            # offset beyond total — fall back to count-only query
            count_result = await self.session.execute(
                select(func.count()).select_from(Membership).where(Membership.org_id == org_id)
            )
            return [], count_result.scalar() or 0
        total = rows[0].total
        return [(row[0], row[1]) for row in rows], total
