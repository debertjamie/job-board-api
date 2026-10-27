from httpx import AsyncClient

from tests.conftest import auth_header, login_token, register_user

JOB_PAYLOAD = {
    "title": "Senior Python Engineer",
    "description": "Build async FastAPI services",
    "location": "Remote",
    "salary_min": 90000,
    "salary_max": 140000,
    "job_type": "full_time",
}


async def _employer_token(client: AsyncClient, email: str = "emp@example.com") -> str:
    await register_user(client, email, "secret123", "employer")
    return await login_token(client, email, "secret123")


async def _applicant_token(client: AsyncClient, email: str = "app@example.com") -> str:
    await register_user(client, email, "secret123", "applicant")
    return await login_token(client, email, "secret123")


async def test_employer_can_create_job(client: AsyncClient) -> None:
    token = await _employer_token(client)
    resp = await client.post("/jobs", json=JOB_PAYLOAD, headers=auth_header(token))
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["title"] == JOB_PAYLOAD["title"]
    assert body["status"] == "open"
    assert "owner_id" in body


async def test_applicant_cannot_create_job(client: AsyncClient) -> None:
    token = await _applicant_token(client)
    resp = await client.post("/jobs", json=JOB_PAYLOAD, headers=auth_header(token))
    assert resp.status_code == 403


async def test_public_job_list_and_filter(client: AsyncClient) -> None:
    token = await _employer_token(client)
    await client.post("/jobs", json=JOB_PAYLOAD, headers=auth_header(token))
    await client.post(
        "/jobs",
        json={**JOB_PAYLOAD, "title": "Part time barista", "job_type": "part_time"},
        headers=auth_header(token),
    )

    # Public listing, no auth.
    resp = await client.get("/jobs")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2

    # Filter by job_type narrows results.
    resp = await client.get("/jobs", params={"job_type": "part_time"})
    assert resp.status_code == 200
    assert resp.json()["total"] == 1

    # Filter by q narrows results.
    resp = await client.get("/jobs", params={"q": "barista"})
    assert resp.json()["total"] == 1


async def test_get_missing_job_returns_404(client: AsyncClient) -> None:
    resp = await client.get("/jobs/9999")
    assert resp.status_code == 404


async def test_owner_can_update_and_delete_non_owner_cannot(client: AsyncClient) -> None:
    owner_token = await _employer_token(client, "owner@example.com")
    other_token = await _employer_token(client, "other@example.com")

    resp = await client.post("/jobs", json=JOB_PAYLOAD, headers=auth_header(owner_token))
    job_id = resp.json()["id"]

    # Non-owner employer cannot update.
    resp = await client.put(
        f"/jobs/{job_id}", json={"title": "Hacked"}, headers=auth_header(other_token)
    )
    assert resp.status_code == 403

    # Owner can update.
    resp = await client.put(
        f"/jobs/{job_id}", json={"status": "closed"}, headers=auth_header(owner_token)
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "closed"

    # Non-owner cannot delete.
    resp = await client.delete(f"/jobs/{job_id}", headers=auth_header(other_token))
    assert resp.status_code == 403

    # Owner can delete.
    resp = await client.delete(f"/jobs/{job_id}", headers=auth_header(owner_token))
    assert resp.status_code == 204
