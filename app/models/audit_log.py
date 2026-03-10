from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, uuid7

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid7)
    org_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(256))
    entity_type: Mapped[str] = mapped_column(String(128))
    entity_id: Mapped[UUID] = mapped_column()
    details: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    organization: Mapped[Organization] = relationship(
        back_populates="audit_logs", lazy="raise"
    )
    user: Mapped[User] = relationship(lazy="raise")

    __table_args__ = (Index("ix_audit_logs_org_id_created_at", "org_id", "created_at"),)
