from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import JobStatus, JobType


class JobCreate(BaseModel):
    title: str
    description: str
    location: str
    salary_min: int | None = None
    salary_max: int | None = None
    job_type: JobType
    status: JobStatus = JobStatus.open


class JobUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    location: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    job_type: JobType | None = None
    status: JobStatus | None = None


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    location: str
    salary_min: int | None
    salary_max: int | None
    job_type: JobType
    status: JobStatus
    owner_id: int
    created_at: datetime


class JobList(BaseModel):
    items: list[JobRead]
    total: int
