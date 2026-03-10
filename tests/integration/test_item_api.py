from httpx import AsyncClient


async def test_create_item_returns_item_id(client: AsyncClient, auth_headers: dict):
    org_id = (
        await client.post(
            "/organization", json={"org_name": "Org"}, headers=auth_headers
        )
    ).json()["org_id"]

    resp = await client.post(
        f"/organizations/{org_id}/item",
        json={"item_details": {"name": "Widget", "price": 9.99}},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert "item_id" in resp.json()


async def test_create_item_requires_membership(client: AsyncClient, auth_headers: dict):
    org_id = (
        await client.post(
            "/organization", json={"org_name": "Org"}, headers=auth_headers
        )
    ).json()["org_id"]

    await client.post(
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

    resp = await client.post(
        f"/organizations/{org_id}/item",
        json={"item_details": {"name": "Widget"}},
        headers={"Authorization": f"Bearer {outsider_token}"},
    )
    assert resp.status_code == 403


async def test_list_items_admin_sees_all(client: AsyncClient, auth_headers: dict):
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
        f"/organizations/{org_id}/item",
        json={"item_details": {"name": "Member Item"}},
        headers=member_headers,
    )
    await client.post(
        f"/organizations/{org_id}/item",
        json={"item_details": {"name": "Admin Item"}},
        headers=auth_headers,
    )

    resp = await client.get(f"/organizations/{org_id}/item", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 2


async def test_list_items_member_sees_own_only(client: AsyncClient, auth_headers: dict):
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
        f"/organizations/{org_id}/item",
        json={"item_details": {"name": "Member Item"}},
        headers=member_headers,
    )
    await client.post(
        f"/organizations/{org_id}/item",
        json={"item_details": {"name": "Admin Item"}},
        headers=auth_headers,
    )

    resp = await client.get(f"/organizations/{org_id}/item", headers=member_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["item_details"]["name"] == "Member Item"


async def test_list_items_pagination(client: AsyncClient, auth_headers: dict):
    org_id = (
        await client.post(
            "/organization", json={"org_name": "Org"}, headers=auth_headers
        )
    ).json()["org_id"]

    for i in range(5):
        await client.post(
            f"/organizations/{org_id}/item",
            json={"item_details": {"index": i}},
            headers=auth_headers,
        )

    resp = await client.get(
        f"/organizations/{org_id}/item",
        params={"limit": 2, "offset": 0},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 5
    assert len(body["items"]) == 2


async def test_list_items_requires_membership(client: AsyncClient, auth_headers: dict):
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
        f"/organizations/{org_id}/item",
        headers={"Authorization": f"Bearer {stranger_token}"},
    )
    assert resp.status_code == 403
