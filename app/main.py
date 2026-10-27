from fastapi import FastAPI

from app.api.routes import applications, auth, jobs

app = FastAPI(title="Job Board API")

app.include_router(auth.router)
app.include_router(jobs.router)
app.include_router(applications.router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
