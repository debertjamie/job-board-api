from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select

from app.api.deps import CurrentUser, DbSession, get_job_or_404, require_role
from app.models.enums import JobStatus, JobType, Role
from app.models.job import Job
from app.models.user import User
from app.schemas.job import JobCreate, JobList, JobRead, JobUpdate

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=JobList)
async def list_jobs(
    db: DbSession,
    q: str | None = None,
    location: str | None = None,
    job_type: JobType | None = None,
    salary_min: int | None = None,
    status: JobStatus | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> JobList:
    filters = []
    if q:
        pattern = f"%{q}%"
        filters.append(or_(Job.title.ilike(pattern), Job.description.ilike(pattern)))
    if location:
        filters.append(Job.location.ilike(f"%{location}%"))
    if job_type is not None:
        filters.append(Job.job_type == job_type)
    if salary_min is not None:
        filters.append(Job.salary_min >= salary_min)
    if status is not None:
        filters.append(Job.status == status)

    total_stmt = select(func.count()).select_from(Job)
    items_stmt = select(Job).order_by(Job.created_at.desc())
    for f in filters:
        total_stmt = total_stmt.where(f)
        items_stmt = items_stmt.where(f)

    total = await db.scalar(total_stmt) or 0
    items = (await db.scalars(items_stmt.limit(limit).offset(offset))).all()
    return JobList(items=list(items), total=total)


@router.get("/{job_id}", response_model=JobRead)
async def get_job(job: Annotated[Job, Depends(get_job_or_404)]) -> Job:
    return job


@router.post("", response_model=JobRead, status_code=status.HTTP_201_CREATED)
async def create_job(
    payload: JobCreate,
    db: DbSession,
    current_user: Annotated[User, Depends(require_role(Role.employer))],
) -> Job:
    job = Job(**payload.model_dump(), owner_id=current_user.id)
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


@router.put("/{job_id}", response_model=JobRead)
async def update_job(
    payload: JobUpdate,
    current_user: CurrentUser,
    db: DbSession,
    job: Annotated[Job, Depends(get_job_or_404)],
) -> Job:
    if job.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the job owner")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(job, field, value)
    await db.commit()
    await db.refresh(job)
    return job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    current_user: CurrentUser,
    db: DbSession,
    job: Annotated[Job, Depends(get_job_or_404)],
) -> None:
    if job.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the job owner")
    await db.delete(job)
    await db.commit()
