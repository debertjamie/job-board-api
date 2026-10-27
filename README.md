# job-board-api

A job board REST API built with Python and FastAPI. This is the "leaner slice": authentication, jobs, and applications. A job belongs directly to its employer (owner) user — there is no separate Company resource in this version.

Users have one of two roles, chosen at registration:

- **employer** — can post, edit, and delete their own jobs and view applications to them.
- **applicant** — can browse jobs and apply to open ones.

## Tech stack

- FastAPI + Uvicorn
- Pydantic v2 + pydantic-settings
- SQLAlchemy 2.0 async ORM + aiosqlite (SQLite)
- Alembic migrations
- JWT auth (python-jose) with bcrypt password hashing (passlib)
- pytest + pytest-asyncio + httpx
- ruff for linting/formatting

## Prerequisites

- Python 3.12
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
# Install dependencies into a local virtualenv
uv sync

# Create your local env file from the example and set a real SECRET_KEY
cp .env.example .env

# Create the database schema
uv run alembic upgrade head
```

`.env` holds `SECRET_KEY`, `DATABASE_URL`, and `ACCESS_TOKEN_EXPIRE_MINUTES`. It is gitignored; `.env.example` is the committed template.

## Run

```bash
uv run uvicorn app.main:app --reload
```

Interactive Swagger UI is available at [`/docs`](http://127.0.0.1:8000/docs) once the server is running.

## Testing and linting

```bash
uv run pytest        # runs against an isolated temp SQLite database
uv run ruff check .
```

## Endpoints

### Auth

- `POST /auth/register` — register with `email`, `password`, `role`; returns the user. 409 on duplicate email.
- `POST /auth/login` — JSON `{email, password}`; returns `{access_token, token_type}`. 401 on bad credentials.

### Jobs

- `GET /jobs` — public. Filters: `q` (title/description search), `location`, `job_type`, `salary_min`, `status`; pagination via `limit` (default 20, max 100) and `offset`. Returns `{items, total}`.
- `GET /jobs/{id}` — public. 404 if missing.
- `POST /jobs` — employer only. Sets the owner to the current user.
- `PUT /jobs/{id}` — job owner only (403 otherwise, 404 if missing).
- `DELETE /jobs/{id}` — job owner only (403/404 as above).

### Applications

- `POST /jobs/{id}/apply` — applicant only. Body: `cover_letter`. 404 if job missing, 400 if the job is closed, 409 if already applied.
- `GET /jobs/{id}/applications` — job owner only. Lists applications for that job.
- `GET /me/applications` — applicant only. Lists the current applicant's own applications.

### Health

- `GET /health` — returns `{"status": "ok"}`.
