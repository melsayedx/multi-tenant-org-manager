from datetime import datetime, timezone
from unittest.mock import AsyncMock

from app.core.utils import uuid7
from app.models.audit_log import AuditLog
from app.services.audit_log import AuditLogService
from app.services.chatbot import ChatbotService


async def test_get_org_logs_returns_logs(mock_audit_repo):
    org_id = uuid7()
    logs = [
        AuditLog(
            id=uuid7(),
            org_id=org_id,
            user_id=uuid7(),
            action="org_created",
            entity_type="organization",
            entity_id=org_id,
            details=None,
            created_at=datetime.now(timezone.utc),
        )
    ]
    mock_audit_repo.get_by_org.return_value = logs

    result = await AuditLogService(mock_audit_repo).get_org_logs(org_id)

    assert result == logs
    mock_audit_repo.get_by_org.assert_called_once_with(org_id)


async def test_get_org_logs_returns_empty_list(mock_audit_repo):
    mock_audit_repo.get_by_org.return_value = []

    result = await AuditLogService(mock_audit_repo).get_org_logs(uuid7())

    assert result == []


async def test_chatbot_generate_answer_calls_llm(mock_audit_repo):
    org_id = uuid7()
    mock_audit_repo.get_today_by_org.return_value = []

    mock_llm = AsyncMock()
    mock_llm.generate = AsyncMock(return_value="No activity today.")

    answer = await ChatbotService(mock_audit_repo, mock_llm).generate_answer(
        org_id, "What happened today?"
    )

    assert answer == "No activity today."
    mock_llm.generate.assert_called_once()


async def test_chatbot_prompt_includes_question(mock_audit_repo):
    org_id = uuid7()
    mock_audit_repo.get_today_by_org.return_value = []

    mock_llm = AsyncMock()
    mock_llm.generate = AsyncMock(return_value="Nothing.")

    service = ChatbotService(mock_audit_repo, mock_llm)
    await service.generate_answer(org_id, "Who created items?")

    prompt = mock_llm.generate.call_args[0][0]
    assert "Who created items?" in prompt


async def test_chatbot_prompt_includes_log_entries(mock_audit_repo):
    org_id = uuid7()
    user_id = uuid7()
    log = AuditLog(
        id=uuid7(),
        org_id=org_id,
        user_id=user_id,
        action="item_created",
        entity_type="item",
        entity_id=uuid7(),
        details={"item_details": {"name": "Widget"}},
        created_at=datetime.now(timezone.utc),
    )
    mock_audit_repo.get_today_by_org.return_value = [log]

    mock_llm = AsyncMock()
    mock_llm.generate = AsyncMock(return_value="1 item was created.")

    service = ChatbotService(mock_audit_repo, mock_llm)
    await service.generate_answer(org_id, "What items were created?")

    prompt = mock_llm.generate.call_args[0][0]
    assert "item_created" in prompt
