from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utcnow, uuid7

if TYPE_CHECKING:
    from app.models.audit_log import AuditLog
    from app.models.item import Item
    from app.models.membership import Membership


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    name: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=utcnow
    )

    memberships: Mapped[list[Membership]] = relationship(
        back_populates="organization", lazy="raise"
    )
    items: Mapped[list[Item]] = relationship(
        back_populates="organization", lazy="raise"
    )
    audit_logs: Mapped[list[AuditLog]] = relationship(
        back_populates="organization", lazy="raise"
    )
