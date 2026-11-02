from httpx import AsyncClient

from tests.conftest import register_user


async def test_register_and_login_happy_path(client: AsyncClient) -> None:
    user = await register_user(client, "alice@example.com", "secret123", "applicant")
    assert user["email"] == "alice@example.com"
    assert user["role"] == "applicant"
    assert "id" in user
    assert "hashed_password" not in user

    resp = await client.post(
        "/auth/login", json={"email": "alice@example.com", "password": "secret123"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


async def test_register_duplicate_email_returns_409(client: AsyncClient) -> None:
    await register_user(client, "bob@example.com", "secret123", "employer")
    resp = await client.post(
        "/auth/register",
        json={"email": "bob@example.com", "password": "other", "role": "employer"},
    )
    assert resp.status_code == 409


async def test_login_bad_credentials_returns_401(client: AsyncClient) -> None:
    await register_user(client, "carol@example.com", "secret123", "applicant")
    resp = await client.post(
        "/auth/login", json={"email": "carol@example.com", "password": "wrong"}
    )
    assert resp.status_code == 401
