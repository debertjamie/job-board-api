from enum import StrEnum


class Role(StrEnum):
    employer = "employer"
    applicant = "applicant"


class JobType(StrEnum):
    full_time = "full_time"
    part_time = "part_time"
    contract = "contract"


class JobStatus(StrEnum):
    open = "open"
    closed = "closed"


class ApplicationStatus(StrEnum):
    submitted = "submitted"
    reviewed = "reviewed"
    accepted = "accepted"
    rejected = "rejected"
