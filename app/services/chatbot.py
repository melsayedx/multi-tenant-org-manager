from typing import TYPE_CHECKING, AsyncGenerator
from uuid import UUID

from app.infrastructure.llm.protocol import LLMProvider
from app.repositories.audit_log import AuditLogRepository

if TYPE_CHECKING:
    from app.models.audit_log import AuditLog


class ChatbotService:
    def __init__(self, audit_repo: AuditLogRepository, llm: LLMProvider) -> None:
        self.audit_repo = audit_repo
        self.llm = llm

    @staticmethod
    def _build_prompt(question: str, logs: list["AuditLog"]) -> str:
        log_text = "\n".join(
            f"- [{log.created_at.isoformat()}] {log.action}: {log.entity_type} "
            f"(id={log.entity_id}) by user {log.user_id}"
            f"{' | details: ' + str(log.details) if log.details else ''}"
            for log in logs
        )
        return (
            "You are an assistant for an organization management system.\n"
            "Below are today's audit logs for this organization:\n\n"
            f"{log_text}\n\n"
            f"Based on these logs, answer the following question:\n{question}"
        )

    async def generate_answer(self, org_id: UUID, question: str) -> str:
        logs = await self.audit_repo.get_today_by_org(org_id)
        prompt = self._build_prompt(question, logs)
        return await self.llm.generate(prompt)

    async def stream_answer(self, org_id: UUID, question: str) -> AsyncGenerator[str, None]:
        logs = await self.audit_repo.get_today_by_org(org_id)
        prompt = self._build_prompt(question, logs)
        async for chunk in self.llm.stream(prompt):
            yield chunk
