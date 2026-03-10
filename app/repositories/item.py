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
        base = select(Item, func.count().over().label("total")).where(Item.org_id == org_id)
        if created_by:
            base = base.where(Item.created_by == created_by)
        rows = (
            await self.session.execute(
                base.order_by(Item.created_at.desc()).offset(offset).limit(limit)
            )
        ).all()
        if not rows:
            # offset beyond total — fall back to count-only query
            count_q = select(func.count()).select_from(Item).where(Item.org_id == org_id)
            if created_by:
                count_q = count_q.where(Item.created_by == created_by)
            return [], (await self.session.execute(count_q)).scalar() or 0
        total = rows[0].total
        return [row[0] for row in rows], total
