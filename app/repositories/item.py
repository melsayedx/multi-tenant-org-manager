from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.item import Item


class ItemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, item: Item) -> Item:
        self.session.add(item)
        await self.session.flush()
        return item

    async def get_by_org(
        self, org_id: UUID, limit: int, offset: int, created_by: UUID | None = None
    ) -> tuple[list[Item], int]:
        base = select(Item).where(Item.org_id == org_id)
        if created_by:
            base = base.where(Item.created_by == created_by)
        count_result = await self.session.execute(
            select(func.count()).select_from(base.subquery())
        )
        total = count_result.scalar() or 0
        result = await self.session.execute(
            base.order_by(Item.created_at.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all()), total
