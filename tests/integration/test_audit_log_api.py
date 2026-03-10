from unittest.mock import AsyncMock, patch

from httpx import AsyncClient


async def _create_org_and_member(
    client: AsyncClient, auth_headers: dict
) -> tuple[str, str]:
    """Helper: creates an org, registers+invites a member, returns (org_id, member_token)."""
    org_id = (
        await client.post(
            "/organization", json={"org_name": "Org"}, headers=auth_headers
        )
    ).json()["org_id"]
    await client.post(
        "/auth/register",
        json={
            "email": "member@test.com",
            "password": "StrongPass123!",
            "full_name": "Member",
        },
    )
    await client.post(
        f"/organization/{org_id}/user",
        json={"email": "member@test.com", "role": "member"},
        headers=auth_headers,
    )
    member_token = (
        await client.post(
            "/auth/login",
            json={"email": "member@test.com", "password": "StrongPass123!"},
        )
    ).json()["access_token"]
    return org_id, member_token


async def test_get_audit_logs_returns_entries(client: AsyncClient, auth_headers: dict):
    org_id = (
        await client.post(
            "/organization", json={"org_name": "Org"}, headers=auth_headers
        )
    ).json()["org_id"]

    resp = await client.get(f"/organizations/{org_id}/audit-logs", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) >= 1
    assert body[0]["action"] == "org_created"


async def test_get_audit_logs_requires_admin(client: AsyncClient, auth_headers: dict):
    org_id, member_token = await _create_org_and_member(client, auth_headers)

    resp = await client.get(
        f"/organizations/{org_id}/audit-logs",
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert resp.status_code == 403


async def test_get_audit_logs_requires_membership(
    client: AsyncClient, auth_headers: dict
):
    org_id = (
        await client.post(
            "/organization", json={"org_name": "Org"}, headers=auth_headers
        )
    ).json()["org_id"]
    await client.post(
        "/auth/register",
        json={
            "email": "stranger@test.com",
            "password": "StrongPass123!",
            "full_name": "Stranger",
        },
    )
    stranger_token = (
        await client.post(
            "/auth/login",
            json={"email": "stranger@test.com", "password": "StrongPass123!"},
        )
    ).json()["access_token"]

    resp = await client.get(
        f"/organizations/{org_id}/audit-logs",
        headers={"Authorization": f"Bearer {stranger_token}"},
    )
    assert resp.status_code == 403


async def test_ask_chatbot_returns_answer(client: AsyncClient, auth_headers: dict):
    org_id = (
        await client.post(
            "/organization", json={"org_name": "Org"}, headers=auth_headers
        )
    ).json()["org_id"]

    with patch(
        "app.api.audit_log.GeminiProvider",
        return_value=AsyncMock(generate=AsyncMock(return_value="One org was created.")),
    ):
        resp = await client.post(
            f"/organizations/{org_id}/audit-logs/ask",
            json={"question": "What happened today?", "stream": False},
            headers=auth_headers,
        )

    assert resp.status_code == 200
    assert resp.json()["answer"] == "One org was created."


async def test_ask_chatbot_requires_admin(client: AsyncClient, auth_headers: dict):
    org_id, member_token = await _create_org_and_member(client, auth_headers)

    resp = await client.post(
        f"/organizations/{org_id}/audit-logs/ask",
        json={"question": "What happened?", "stream": False},
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert resp.status_code == 403


async def test_ask_chatbot_empty_question_returns_422(
    client: AsyncClient, auth_headers: dict
):
    org_id = (
        await client.post(
            "/organization", json={"org_name": "Org"}, headers=auth_headers
        )
    ).json()["org_id"]

    resp = await client.post(
        f"/organizations/{org_id}/audit-logs/ask",
        json={"question": "", "stream": False},
        headers=auth_headers,
    )
    assert resp.status_code == 422
