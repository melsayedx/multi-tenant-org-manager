import pytest
from httpx import AsyncClient


async def test_register_returns_user(client: AsyncClient):
    resp = await client.post(
        "/auth/register",
        json={
            "email": "user@test.com",
            "password": "StrongPass123!",
            "full_name": "John Doe",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "user@test.com"
    assert body["full_name"] == "John Doe"
    assert "id" in body
    assert "created_at" in body
    assert "password" not in body


async def test_login_returns_token(client: AsyncClient):
    await client.post(
        "/auth/register",
        json={
            "email": "login@test.com",
            "password": "StrongPass123!",
            "full_name": "Login User",
        },
    )
    resp = await client.post(
        "/auth/login",
        json={"email": "login@test.com", "password": "StrongPass123!"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


async def test_register_duplicate_email_returns_409(client: AsyncClient):
    payload = {
        "email": "dup@test.com",
        "password": "StrongPass123!",
        "full_name": "User",
    }
    await client.post("/auth/register", json=payload)
    resp = await client.post("/auth/register", json=payload)
    assert resp.status_code == 409


async def test_login_wrong_password_returns_401(client: AsyncClient):
    await client.post(
        "/auth/register",
        json={
            "email": "pass@test.com",
            "password": "StrongPass123!",
            "full_name": "User",
        },
    )
    resp = await client.post(
        "/auth/login",
        json={"email": "pass@test.com", "password": "WrongPassword"},
    )
    assert resp.status_code == 401


async def test_login_unknown_email_returns_401(client: AsyncClient):
    resp = await client.post(
        "/auth/login",
        json={"email": "nobody@test.com", "password": "StrongPass123!"},
    )
    assert resp.status_code == 401


async def test_login_invalid_email_format_returns_422(client: AsyncClient):
    resp = await client.post(
        "/auth/login",
        json={"email": "not-an-email", "password": "StrongPass123!"},
    )
    assert resp.status_code == 422


async def test_register_short_password_returns_422(client: AsyncClient):
    resp = await client.post(
        "/auth/register",
        json={"email": "short@test.com", "password": "short", "full_name": "User"},
    )
    assert resp.status_code == 422
