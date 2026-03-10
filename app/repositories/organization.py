from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.organization import Organization


class OrganizationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, org: Organization) -> Organization:
        self.session.add(org)
        await self.session.flush()
        return org

    async def get_by_id(self, org_id: UUID) -> Organization | None:
        return await self.session.get(Organization, org_id)
