from uuid import UUID

from app.models.audit_log import AuditLog
from app.repositories.audit_log import AuditLogRepository


class AuditLogService:
    def __init__(self, audit_repo: AuditLogRepository) -> None:
        self.audit_repo = audit_repo

    async def get_org_logs(self, org_id: UUID) -> list[AuditLog]:
        return await self.audit_repo.get_by_org(org_id)
