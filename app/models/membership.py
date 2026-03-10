from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User


class Role(str, enum.Enum):
    ADMIN = "admin"
    MEMBER = "member"


class Membership(Base):
    __tablename__ = "memberships"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    org_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id"), primary_key=True
    )
    role: Mapped[Role] = mapped_column(default=Role.MEMBER)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped[User] = relationship(back_populates="memberships", lazy="raise")
    organization: Mapped[Organization] = relationship(
        back_populates="memberships", lazy="raise"
    )

    __table_args__ = (Index("ix_membership_org_created", "org_id", "created_at"),)
