from datetime import datetime, timedelta, timezone

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from src.db.models import BatchJob, Prediction


def get_prediction_counts(db: Session) -> dict:
    total_predictions = db.scalar(select(func.count(Prediction.id))) or 0
    valid_predictions = db.scalar(
        select(func.count(Prediction.id)).where(Prediction.is_valid.is_(True))
    ) or 0
    invalid_predictions = db.scalar(
        select(func.count(Prediction.id)).where(Prediction.is_valid.is_(False))
    ) or 0
    review_count = db.scalar(
        select(func.count(Prediction.id)).where(Prediction.review.is_(True))
    ) or 0

    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    recent_predictions = db.scalar(
        select(func.count(Prediction.id)).where(Prediction.created_at >= cutoff)
    ) or 0

    latest_prediction_created_at = db.scalar(
        select(Prediction.created_at).order_by(desc(Prediction.created_at)).limit(1)
    )

    return {
        "total_predictions": int(total_predictions),
        "valid_predictions": int(valid_predictions),
        "invalid_predictions": int(invalid_predictions),
        "review_count": int(review_count),
        "recent_predictions": int(recent_predictions),
        "latest_prediction_created_at": latest_prediction_created_at,
    }


def get_batch_job_counts(db: Session) -> dict:
    batch_jobs_count = db.scalar(select(func.count(BatchJob.id))) or 0
    completed_batch_jobs = db.scalar(
        select(func.count(BatchJob.id)).where(BatchJob.status == "completed")
    ) or 0
    failed_batch_jobs = db.scalar(
        select(func.count(BatchJob.id)).where(BatchJob.status == "failed")
    ) or 0
    latest_batch_created_at = db.scalar(
        select(BatchJob.created_at).order_by(desc(BatchJob.created_at)).limit(1)
    )

    return {
        "batch_jobs_count": int(batch_jobs_count),
        "completed_batch_jobs": int(completed_batch_jobs),
        "failed_batch_jobs": int(failed_batch_jobs),
        "latest_batch_created_at": latest_batch_created_at,
    }


def list_priority_cases(
    db: Session,
    *,
    limit: int,
    offset: int,
    only_review: bool,
) -> list[Prediction]:
    stmt = select(Prediction).where(Prediction.is_valid.is_(True))
    if only_review:
        stmt = stmt.where(Prediction.review.is_(True))

    stmt = stmt.order_by(Prediction.proba_fraud.desc().nullslast(), Prediction.created_at.desc())
    stmt = stmt.limit(limit).offset(offset)
    return list(db.scalars(stmt).all())
