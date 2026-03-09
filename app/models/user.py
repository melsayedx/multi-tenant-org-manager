from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

from sqlalchemy import CHAR, Computed, Index, String, func
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid_utils import uuid7

from app.models.base import Base, utcnow

if TYPE_CHECKING:
    from app.models.item import Item
    from app.models.membership import Membership


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    email: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(64))
    password: Mapped[str] = mapped_column(CHAR(128))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=utcnow
    )
    search_vector: Mapped[Optional[Any]] = mapped_column(
        TSVECTOR,
        Computed(
            "to_tsvector('english', coalesce(full_name, '') || ' ' || coalesce(email, ''))",
            persisted=True,
        ),
    )

    memberships: Mapped[list[Membership]] = relationship(
        back_populates="user", lazy="raise"
    )
    items: Mapped[list[Item]] = relationship(
        back_populates="creator", foreign_keys="Item.created_by", lazy="raise"
    )

    __table_args__ = (
        Index("ix_user_search_vector", "search_vector", postgresql_using="gin"),
    )
