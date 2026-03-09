from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, func, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_utils import uuid7

from app.models.base import Base, utcnow

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User


class Item(Base):
    __tablename__ = "items"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    org_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    item_details: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=utcnow)

    organization: Mapped[Organization] = relationship(back_populates="items", lazy="raise")
    creator: Mapped[User] = relationship(
        back_populates="items", foreign_keys=[created_by], lazy="raise"
    )
