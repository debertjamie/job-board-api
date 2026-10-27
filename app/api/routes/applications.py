from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, get_job_or_404, require_role
from app.models.application import Application
from app.models.enums import JobStatus, Role
from app.models.job import Job
from app.models.user import User
from app.schemas.application import ApplicationCreate, ApplicationRead

router = APIRouter(tags=["applications"])


@router.post(
    "/jobs/{job_id}/apply",
    response_model=ApplicationRead,
    status_code=status.HTTP_201_CREATED,
)
async def apply_to_job(
    payload: ApplicationCreate,
    db: DbSession,
    current_user: Annotated[User, Depends(require_role(Role.applicant))],
    job: Annotated[Job, Depends(get_job_or_404)],
) -> Application:
    if job.status == JobStatus.closed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Job is closed"
        )
    existing = await db.scalar(
        select(Application).where(
            Application.job_id == job.id,
            Application.applicant_id == current_user.id,
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Already applied to this job"
        )
    application = Application(
        job_id=job.id,
        applicant_id=current_user.id,
        cover_letter=payload.cover_letter,
    )
    db.add(application)
    await db.commit()
    await db.refresh(application)
    return application


@router.get("/jobs/{job_id}/applications", response_model=list[ApplicationRead])
async def list_job_applications(
    current_user: CurrentUser,
    db: DbSession,
    job: Annotated[Job, Depends(get_job_or_404)],
) -> list[Application]:
    if job.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the job owner")
    result = await db.scalars(
        select(Application)
        .where(Application.job_id == job.id)
        .order_by(Application.created_at.desc())
    )
    return list(result.all())


@router.get("/me/applications", response_model=list[ApplicationRead])
async def list_my_applications(
    current_user: Annotated[User, Depends(require_role(Role.applicant))],
    db: DbSession,
) -> list[Application]:
    result = await db.scalars(
        select(Application)
        .where(Application.applicant_id == current_user.id)
        .order_by(Application.created_at.desc())
    )
    return list(result.all())
