from uuid import UUID

from app.models.audit_log import AuditLog
from app.models.item import Item
from app.models.membership import Role
from app.repositories.audit_log import AuditLogRepository
from app.repositories.item import ItemRepository


class ItemService:
    def __init__(
        self, item_repo: ItemRepository, audit_repo: AuditLogRepository
    ) -> None:
        self.item_repo = item_repo
        self.audit_repo = audit_repo

    async def create_item(
        self, org_id: UUID, user_id: UUID, item_details: dict
    ) -> Item:
        item = Item(org_id=org_id, created_by=user_id, item_details=item_details)
        item = await self.item_repo.create(item)
        await self.audit_repo.create(
            AuditLog(
                org_id=org_id,
                user_id=user_id,
                action="item_created",
                entity_type="item",
                entity_id=item.id,
                details={"item_details": item_details},
            )
        )
        return item

    async def list_items(
        self, org_id: UUID, user_id: UUID, role: Role, limit: int, offset: int
    ) -> tuple[list[Item], int]:
        created_by = None if role == Role.ADMIN else user_id
        return await self.item_repo.get_by_org(org_id, limit, offset, created_by)
