from datetime import datetime

from sqlalchemy import asc, desc, select
from sqlalchemy.orm import Session

from src.db.models import BatchJob


def create_batch_job(
    db: Session,
    *,
    filename: str,
    status: str,
    total_rows: int,
    valid_rows: int,
    invalid_rows: int,
    review_count: int,
    original_path: str | None = None,
    output_path: str | None = None,
    created_by_user_id: int | None = None,
    error_message: str | None = None,
) -> BatchJob:
    batch_job = BatchJob(
        filename=filename,
        original_path=original_path,
        output_path=output_path,
        status=status,
        total_rows=total_rows,
        valid_rows=valid_rows,
        invalid_rows=invalid_rows,
        review_count=review_count,
        error_message=error_message,
        created_by_user_id=created_by_user_id,
    )
    db.add(batch_job)
    return batch_job


def finalize_batch_job(
    batch_job: BatchJob,
    *,
    status: str,
    total_rows: int,
    valid_rows: int,
    invalid_rows: int,
    review_count: int,
    finished_at: datetime,
    error_message: str | None = None,
) -> BatchJob:
    batch_job.status = status
    batch_job.total_rows = total_rows
    batch_job.valid_rows = valid_rows
    batch_job.invalid_rows = invalid_rows
    batch_job.review_count = review_count
    batch_job.finished_at = finished_at
    batch_job.error_message = error_message
    return batch_job


def list_batch_jobs(
    db: Session,
    *,
    limit: int,
    offset: int,
    status: str | None = None,
    order: str = "desc",
) -> list[BatchJob]:
    stmt = select(BatchJob)
    if status is not None:
        stmt = stmt.where(BatchJob.status == status)

    order_clause = desc(BatchJob.created_at) if order.lower() != "asc" else asc(BatchJob.created_at)
    stmt = stmt.order_by(order_clause).limit(limit).offset(offset)
    return list(db.scalars(stmt).all())


def get_batch_job_by_id(db: Session, batch_job_id: int) -> BatchJob | None:
    stmt = select(BatchJob).where(BatchJob.id == batch_job_id)
    return db.scalar(stmt)
