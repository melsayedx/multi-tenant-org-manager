from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, log: AuditLog) -> AuditLog:
        self.session.add(log)
        await self.session.flush()
        return log

    async def get_by_org(self, org_id: UUID) -> list[AuditLog]:
        result = await self.session.execute(
            select(AuditLog)
            .where(AuditLog.org_id == org_id)
            .order_by(AuditLog.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_today_by_org(self, org_id: UUID) -> list[AuditLog]:
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        result = await self.session.execute(
            select(AuditLog)
            .where(AuditLog.org_id == org_id, AuditLog.created_at >= today_start)
            .order_by(AuditLog.created_at.desc())
        )
        return list(result.scalars().all())
