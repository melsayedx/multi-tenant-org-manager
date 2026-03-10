from httpx import AsyncClient


async def test_create_organization_returns_org_id(
    client: AsyncClient, auth_headers: dict
):
    resp = await client.post(
        "/organization",
        json={"org_name": "My Org"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert "org_id" in resp.json()


async def test_create_organization_requires_auth(client: AsyncClient):
    resp = await client.post("/organization", json={"org_name": "My Org"})
    assert resp.status_code == 401


async def test_invite_user_success(client: AsyncClient, auth_headers: dict):
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

    resp = await client.post(
        f"/organization/{org_id}/user",
        json={"email": "member@test.com", "role": "member"},
        headers=auth_headers,
    )
    assert resp.status_code == 201


async def test_invite_nonexistent_user_returns_404(
    client: AsyncClient, auth_headers: dict
):
    org_id = (
        await client.post(
            "/organization", json={"org_name": "Org"}, headers=auth_headers
        )
    ).json()["org_id"]

    resp = await client.post(
        f"/organization/{org_id}/user",
        json={"email": "nobody@test.com", "role": "member"},
        headers=auth_headers,
    )
    assert resp.status_code == 404


async def test_invite_existing_member_returns_409(
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

    resp = await client.post(
        f"/organization/{org_id}/user",
        json={"email": "member@test.com", "role": "member"},
        headers=auth_headers,
    )
    assert resp.status_code == 409


async def test_invite_requires_admin(client: AsyncClient, auth_headers: dict):
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
    member_headers = {"Authorization": f"Bearer {member_token}"}

    await client.post(
        "/auth/register",
        json={
            "email": "third@test.com",
            "password": "StrongPass123!",
            "full_name": "Third",
        },
    )
    resp = await client.post(
        f"/organization/{org_id}/user",
        json={"email": "third@test.com", "role": "member"},
        headers=member_headers,
    )
    assert resp.status_code == 403


async def test_non_member_cannot_invite(client: AsyncClient, auth_headers: dict):
    org_id = (
        await client.post(
            "/organization", json={"org_name": "Org"}, headers=auth_headers
        )
    ).json()["org_id"]

    outsider_token = await client.post(
        "/auth/register",
        json={
            "email": "outsider@test.com",
            "password": "StrongPass123!",
            "full_name": "Out",
        },
    )
    outsider_token = (
        await client.post(
            "/auth/login",
            json={"email": "outsider@test.com", "password": "StrongPass123!"},
        )
    ).json()["access_token"]
    outsider_headers = {"Authorization": f"Bearer {outsider_token}"}

    resp = await client.post(
        f"/organization/{org_id}/user",
        json={"email": "outsider@test.com", "role": "member"},
        headers=outsider_headers,
    )
    assert resp.status_code == 403


async def test_list_users_returns_all_members(client: AsyncClient, auth_headers: dict):
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

    resp = await client.get(f"/organizations/{org_id}/users", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert len(body["users"]) == 2
    roles = {u["role"] for u in body["users"]}
    assert roles == {"admin", "member"}


async def test_list_users_requires_admin(client: AsyncClient, auth_headers: dict):
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

    resp = await client.get(
        f"/organizations/{org_id}/users",
        headers={"Authorization": f"Bearer {member_token}"},
    )
    assert resp.status_code == 403


async def test_search_users_returns_matching(client: AsyncClient, auth_headers: dict):
    org_id = (
        await client.post(
            "/organization", json={"org_name": "Org"}, headers=auth_headers
        )
    ).json()["org_id"]

    await client.post(
        "/auth/register",
        json={
            "email": "alice@test.com",
            "password": "StrongPass123!",
            "full_name": "Alice Smith",
        },
    )
    await client.post(
        f"/organization/{org_id}/user",
        json={"email": "alice@test.com", "role": "member"},
        headers=auth_headers,
    )

    resp = await client.get(
        f"/organizations/{org_id}/users/search",
        params={"q": "Alice"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["full_name"] == "Alice Smith"


async def test_search_users_no_match_returns_empty(
    client: AsyncClient, auth_headers: dict
):
    org_id = (
        await client.post(
            "/organization", json={"org_name": "Org"}, headers=auth_headers
        )
    ).json()["org_id"]

    resp = await client.get(
        f"/organizations/{org_id}/users/search",
        params={"q": "nobody"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 0
