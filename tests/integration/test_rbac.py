"""
Cross-cutting RBAC and org isolation tests.

Scenarios covered:
1. Member cannot use admin-only endpoints
2. Non-member cannot access any org endpoint
3. Org A data is not visible from Org B context
4. Admin sees all items; member sees only their own
"""


from httpx import AsyncClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _register_and_login(client: AsyncClient, email: str, name: str) -> str:
    await client.post(
        "/auth/register",
        json={"email": email, "password": "StrongPass123!", "full_name": name},
    )
    return (
        await client.post(
            "/auth/login",
            json={"email": email, "password": "StrongPass123!"},
        )
    ).json()["access_token"]


async def _create_org(client: AsyncClient, headers: dict, name: str = "Org") -> str:
    return (
        await client.post("/organization", json={"org_name": name}, headers=headers)
    ).json()["org_id"]


async def _invite(
    client: AsyncClient, org_id: str, email: str, role: str, headers: dict
):
    await client.post(
        f"/organization/{org_id}/user",
        json={"email": email, "role": role},
        headers=headers,
    )


# ---------------------------------------------------------------------------
# 1. Member cannot use admin-only endpoints
# ---------------------------------------------------------------------------


async def test_member_cannot_invite_users(client: AsyncClient, auth_headers: dict):
    org_id = await _create_org(client, auth_headers)
    member_token = await _register_and_login(client, "member@test.com", "Member")
    await _invite(client, org_id, "member@test.com", "member", auth_headers)
    member_headers = {"Authorization": f"Bearer {member_token}"}

    third_token = await _register_and_login(client, "third@test.com", "Third")
    resp = await client.post(
        f"/organization/{org_id}/user",
        json={"email": "third@test.com", "role": "member"},
        headers=member_headers,
    )
    assert resp.status_code == 403


async def test_member_cannot_list_users(client: AsyncClient, auth_headers: dict):
    org_id = await _create_org(client, auth_headers)
    member_token = await _register_and_login(client, "member@test.com", "Member")
    await _invite(client, org_id, "member@test.com", "member", auth_headers)
    member_headers = {"Authorization": f"Bearer {member_token}"}

    resp = await client.get(f"/organizations/{org_id}/users", headers=member_headers)
    assert resp.status_code == 403


async def test_member_cannot_search_users(client: AsyncClient, auth_headers: dict):
    org_id = await _create_org(client, auth_headers)
    member_token = await _register_and_login(client, "member@test.com", "Member")
    await _invite(client, org_id, "member@test.com", "member", auth_headers)
    member_headers = {"Authorization": f"Bearer {member_token}"}

    resp = await client.get(
        f"/organizations/{org_id}/users/search",
        params={"q": "Member"},
        headers=member_headers,
    )
    assert resp.status_code == 403


async def test_member_cannot_view_audit_logs(client: AsyncClient, auth_headers: dict):
    org_id = await _create_org(client, auth_headers)
    member_token = await _register_and_login(client, "member@test.com", "Member")
    await _invite(client, org_id, "member@test.com", "member", auth_headers)
    member_headers = {"Authorization": f"Bearer {member_token}"}

    resp = await client.get(
        f"/organizations/{org_id}/audit-logs", headers=member_headers
    )
    assert resp.status_code == 403


async def test_member_cannot_ask_chatbot(client: AsyncClient, auth_headers: dict):
    org_id = await _create_org(client, auth_headers)
    member_token = await _register_and_login(client, "member@test.com", "Member")
    await _invite(client, org_id, "member@test.com", "member", auth_headers)
    member_headers = {"Authorization": f"Bearer {member_token}"}

    resp = await client.post(
        f"/organizations/{org_id}/audit-logs/ask",
        json={"question": "What happened?", "stream": False},
        headers=member_headers,
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# 2. Non-member cannot access any org endpoint
# ---------------------------------------------------------------------------


async def test_non_member_cannot_invite(client: AsyncClient, auth_headers: dict):
    org_id = await _create_org(client, auth_headers)
    outsider_token = await _register_and_login(client, "outsider@test.com", "Outsider")
    outsider_headers = {"Authorization": f"Bearer {outsider_token}"}

    await _register_and_login(client, "target@test.com", "Target")
    resp = await client.post(
        f"/organization/{org_id}/user",
        json={"email": "target@test.com", "role": "member"},
        headers=outsider_headers,
    )
    assert resp.status_code == 403


async def test_non_member_cannot_list_users(client: AsyncClient, auth_headers: dict):
    org_id = await _create_org(client, auth_headers)
    outsider_token = await _register_and_login(client, "outsider@test.com", "Outsider")
    outsider_headers = {"Authorization": f"Bearer {outsider_token}"}

    resp = await client.get(f"/organizations/{org_id}/users", headers=outsider_headers)
    assert resp.status_code == 403


async def test_non_member_cannot_create_item(client: AsyncClient, auth_headers: dict):
    org_id = await _create_org(client, auth_headers)
    outsider_token = await _register_and_login(client, "outsider@test.com", "Outsider")
    outsider_headers = {"Authorization": f"Bearer {outsider_token}"}

    resp = await client.post(
        f"/organizations/{org_id}/item",
        json={"item_details": {"name": "Stolen"}},
        headers=outsider_headers,
    )
    assert resp.status_code == 403


async def test_non_member_cannot_list_items(client: AsyncClient, auth_headers: dict):
    org_id = await _create_org(client, auth_headers)
    outsider_token = await _register_and_login(client, "outsider@test.com", "Outsider")
    outsider_headers = {"Authorization": f"Bearer {outsider_token}"}

    resp = await client.get(f"/organizations/{org_id}/item", headers=outsider_headers)
    assert resp.status_code == 403


async def test_non_member_cannot_view_audit_logs(
    client: AsyncClient, auth_headers: dict
):
    org_id = await _create_org(client, auth_headers)
    outsider_token = await _register_and_login(client, "outsider@test.com", "Outsider")
    outsider_headers = {"Authorization": f"Bearer {outsider_token}"}

    resp = await client.get(
        f"/organizations/{org_id}/audit-logs", headers=outsider_headers
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# 3. Org isolation — User A cannot see Org B's data
# ---------------------------------------------------------------------------


async def test_user_cannot_access_other_orgs_items(
    client: AsyncClient, auth_headers: dict
):
    """Admin of Org A should get 403 on Org B's item endpoint."""
    org_a_id = await _create_org(client, auth_headers, "Org A")

    user_b_token = await _register_and_login(client, "userb@test.com", "User B")
    user_b_headers = {"Authorization": f"Bearer {user_b_token}"}
    org_b_id = await _create_org(client, user_b_headers, "Org B")

    # admin@test.com is admin of Org A but not a member of Org B
    resp = await client.get(f"/organizations/{org_b_id}/item", headers=auth_headers)
    assert resp.status_code == 403


async def test_user_cannot_access_other_orgs_audit_logs(
    client: AsyncClient, auth_headers: dict
):
    org_a_id = await _create_org(client, auth_headers, "Org A")

    user_b_token = await _register_and_login(client, "userb@test.com", "User B")
    user_b_headers = {"Authorization": f"Bearer {user_b_token}"}
    org_b_id = await _create_org(client, user_b_headers, "Org B")

    resp = await client.get(
        f"/organizations/{org_b_id}/audit-logs", headers=auth_headers
    )
    assert resp.status_code == 403


async def test_items_are_isolated_between_orgs(client: AsyncClient, auth_headers: dict):
    """Items created in Org A must not appear when listing Org B's items."""
    org_a_id = await _create_org(client, auth_headers, "Org A")
    await client.post(
        f"/organizations/{org_a_id}/item",
        json={"item_details": {"name": "Org A Item"}},
        headers=auth_headers,
    )

    user_b_token = await _register_and_login(client, "userb@test.com", "User B")
    user_b_headers = {"Authorization": f"Bearer {user_b_token}"}
    org_b_id = await _create_org(client, user_b_headers, "Org B")

    resp = await client.get(f"/organizations/{org_b_id}/item", headers=user_b_headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


async def test_audit_logs_are_isolated_between_orgs(
    client: AsyncClient, auth_headers: dict
):
    """Org B admin should only see Org B's audit logs, not Org A's."""
    org_a_id = await _create_org(client, auth_headers, "Org A")

    user_b_token = await _register_and_login(client, "userb@test.com", "User B")
    user_b_headers = {"Authorization": f"Bearer {user_b_token}"}
    org_b_id = await _create_org(client, user_b_headers, "Org B")

    resp = await client.get(
        f"/organizations/{org_b_id}/audit-logs", headers=user_b_headers
    )
    assert resp.status_code == 200
    logs = resp.json()
    # Only Org B's org_created log — none from Org A
    assert all(log["action"] == "org_created" for log in logs)
    assert len(logs) == 1


# ---------------------------------------------------------------------------
# 4. Admin sees all items; member sees only own (RBAC filter)
# ---------------------------------------------------------------------------


async def test_admin_sees_all_items_from_all_members(
    client: AsyncClient, auth_headers: dict
):
    org_id = await _create_org(client, auth_headers)

    member_token = await _register_and_login(client, "member@test.com", "Member")
    await _invite(client, org_id, "member@test.com", "member", auth_headers)
    member_headers = {"Authorization": f"Bearer {member_token}"}

    await client.post(
        f"/organizations/{org_id}/item",
        json={"item_details": {"owner": "admin"}},
        headers=auth_headers,
    )
    await client.post(
        f"/organizations/{org_id}/item",
        json={"item_details": {"owner": "member"}},
        headers=member_headers,
    )

    resp = await client.get(f"/organizations/{org_id}/item", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 2


async def test_member_only_sees_own_items_not_admin_items(
    client: AsyncClient, auth_headers: dict
):
    org_id = await _create_org(client, auth_headers)

    member_token = await _register_and_login(client, "member@test.com", "Member")
    await _invite(client, org_id, "member@test.com", "member", auth_headers)
    member_headers = {"Authorization": f"Bearer {member_token}"}

    await client.post(
        f"/organizations/{org_id}/item",
        json={"item_details": {"owner": "admin"}},
        headers=auth_headers,
    )
    await client.post(
        f"/organizations/{org_id}/item",
        json={"item_details": {"owner": "member"}},
        headers=member_headers,
    )

    resp = await client.get(f"/organizations/{org_id}/item", headers=member_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["item_details"]["owner"] == "member"
