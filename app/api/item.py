from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, require_membership
from app.infrastructure.database import get_db
from app.models.membership import Membership
from app.models.user import User
from app.repositories.audit_log import AuditLogRepository
from app.repositories.item import ItemRepository
from app.schemas.item import ItemCreate, ItemDetail, ItemResponse, PaginatedItems
from app.services.item import ItemService

router = APIRouter(prefix="/organizations/{org_id}", tags=["items"])


def _item_service(db: AsyncSession) -> ItemService:
    return ItemService(ItemRepository(db), AuditLogRepository(db))


@router.post("/item", response_model=ItemResponse, status_code=201)
async def create_item(
    org_id: UUID,
    data: ItemCreate,
    membership: Membership = Depends(require_membership),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = await _item_service(db).create_item(org_id, user.id, data.item_details)
    return ItemResponse(item_id=item.id)


@router.get("/item", response_model=PaginatedItems)
async def list_items(
    org_id: UUID,
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    membership: Membership = Depends(require_membership),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    items, total = await _item_service(db).list_items(
        org_id, user.id, membership.role, limit, offset
    )
    return PaginatedItems(
        items=[
            ItemDetail(
                id=i.id,
                item_details=i.item_details,
                created_by=i.created_by,
                created_at=i.created_at,
            )
            for i in items
        ],
        total=total,
        limit=limit,
        offset=offset,
    )
