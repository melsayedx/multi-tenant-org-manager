import re
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.membership import Membership
from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, user: User) -> User:
        self.session.add(user)
        # flush to assign the DB-generated id without committing the transaction
        await self.session.flush()
        return user

    async def get_by_email(self, email: str) -> User | None:
        return await self.session.scalar(select(User).where(User.email == email))

    async def get_by_id(self, user_id: UUID) -> User | None:
        # uses session identity map cache when the object is already loaded
        return await self.session.get(User, user_id)

    # NOTE: the admin making the request is not excluded from search results
    async def search_in_org(self, org_id: UUID, query: str) -> list:
        # split on non-word characters and drop empty tokens
        words = [w for w in re.split(r"\W+", query.strip()) if w]
        if not words:
            return []

        # build a prefix-match tsquery: e.g. "jo & do:*" matches "john doe"
        tsquery_str = " & ".join(f"{word}:*" for word in words)
        base = (
            select(User, Membership.role)
            .join(Membership, Membership.user_id == User.id)
            .where(Membership.org_id == org_id)
            # @@ operator checks whether the tsvector matches the tsquery
            .where(User.search_vector.op("@@")(func.to_tsquery("english", tsquery_str)))
        )
        result = await self.session.execute(base)
        return list(result.all())
