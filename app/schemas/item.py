from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ItemCreate(BaseModel):
    item_details: dict


class ItemResponse(BaseModel):
    item_id: UUID


class ItemDetail(BaseModel):
    id: UUID
    item_details: dict
    created_by: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedItems(BaseModel):
    items: list[ItemDetail]
    total: int
    limit: int
    offset: int
