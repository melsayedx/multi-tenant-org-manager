from typing import AsyncIterator
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_admin
from app.infrastructure.database import get_db
from app.infrastructure.llm.gemini_provider import GeminiProvider
from app.models.membership import Membership
from app.repositories.audit_log import AuditLogRepository
from app.schemas.audit_log import AuditLogResponse, ChatbotRequest, ChatbotResponse
from app.services.audit_log import AuditLogService
from app.services.chatbot import ChatbotService

router = APIRouter(prefix="/organizations/{org_id}", tags=["audit-logs"])


async def _sse(stream: AsyncIterator[str]) -> AsyncIterator[str]:
    """Wrap an async text stream into proper Server-Sent Events format."""
    async for chunk in stream:
        yield f"data: {chunk}\n\n"


@router.get("/audit-logs", response_model=list[AuditLogResponse])
async def get_audit_logs(
    org_id: UUID,
    _: Membership = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await AuditLogService(AuditLogRepository(db)).get_org_logs(org_id)


@router.post("/audit-logs/ask")
async def ask_chatbot(
    org_id: UUID,
    data: ChatbotRequest,
    _: Membership = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    llm = GeminiProvider()
    service = ChatbotService(AuditLogRepository(db), llm)
    history = [h.model_dump() for h in data.history] or None

    if data.stream:
        return StreamingResponse(
            _sse(service.stream_answer(org_id, data.question, history)),
            media_type="text/event-stream",
        )
    answer = await service.generate_answer(org_id, data.question, history)
    return ChatbotResponse(answer=answer)
