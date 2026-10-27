from httpx import AsyncClient

from tests.conftest import auth_header, login_token, register_user

JOB_PAYLOAD = {
    "title": "Backend Engineer",
    "description": "Async APIs",
    "location": "Remote",
    "job_type": "full_time",
}


async def _setup_employer_with_job(
    client: AsyncClient, job_overrides: dict | None = None
) -> tuple[str, int]:
    await register_user(client, "emp@example.com", "secret123", "employer")
    token = await login_token(client, "emp@example.com", "secret123")
    payload = {**JOB_PAYLOAD, **(job_overrides or {})}
    resp = await client.post("/jobs", json=payload, headers=auth_header(token))
    return token, resp.json()["id"]


async def _applicant_token(client: AsyncClient, email: str = "app@example.com") -> str:
    await register_user(client, email, "secret123", "applicant")
    return await login_token(client, email, "secret123")


async def test_applicant_can_apply_to_open_job(client: AsyncClient) -> None:
    _, job_id = await _setup_employer_with_job(client)
    token = await _applicant_token(client)
    resp = await client.post(
        f"/jobs/{job_id}/apply",
        json={"cover_letter": "Please hire me"},
        headers=auth_header(token),
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["job_id"] == job_id
    assert body["status"] == "submitted"


async def test_duplicate_apply_returns_409(client: AsyncClient) -> None:
    _, job_id = await _setup_employer_with_job(client)
    token = await _applicant_token(client)
    header = auth_header(token)
    await client.post(f"/jobs/{job_id}/apply", json={"cover_letter": "a"}, headers=header)
    resp = await client.post(
        f"/jobs/{job_id}/apply", json={"cover_letter": "b"}, headers=header
    )
    assert resp.status_code == 409


async def test_apply_to_closed_job_returns_400(client: AsyncClient) -> None:
    _, job_id = await _setup_employer_with_job(client, {"status": "closed"})
    token = await _applicant_token(client)
    resp = await client.post(
        f"/jobs/{job_id}/apply",
        json={"cover_letter": "hi"},
        headers=auth_header(token),
    )
    assert resp.status_code == 400


async def test_employer_cannot_apply(client: AsyncClient) -> None:
    emp_token, job_id = await _setup_employer_with_job(client)
    resp = await client.post(
        f"/jobs/{job_id}/apply",
        json={"cover_letter": "hi"},
        headers=auth_header(emp_token),
    )
    assert resp.status_code == 403


async def test_job_owner_lists_applications_non_owner_cannot(client: AsyncClient) -> None:
    owner_token, job_id = await _setup_employer_with_job(client)
    app_token = await _applicant_token(client)
    await client.post(
        f"/jobs/{job_id}/apply",
        json={"cover_letter": "hi"},
        headers=auth_header(app_token),
    )

    # Owner can list.
    resp = await client.get(f"/jobs/{job_id}/applications", headers=auth_header(owner_token))
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    # A different employer cannot list.
    await register_user(client, "other@example.com", "secret123", "employer")
    other_token = await login_token(client, "other@example.com", "secret123")
    resp = await client.get(f"/jobs/{job_id}/applications", headers=auth_header(other_token))
    assert resp.status_code == 403


async def test_me_applications_returns_own(client: AsyncClient) -> None:
    _, job_id = await _setup_employer_with_job(client)
    token = await _applicant_token(client)
    await client.post(
        f"/jobs/{job_id}/apply",
        json={"cover_letter": "hi"},
        headers=auth_header(token),
    )
    resp = await client.get("/me/applications", headers=auth_header(token))
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["job_id"] == job_id
