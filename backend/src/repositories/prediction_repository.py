from sqlalchemy import asc, desc, select
from sqlalchemy.orm import Session

from src.db.models import Prediction


def create_prediction(
    db: Session,
    *,
    batch_job_id: int | None,
    model_version_id: int | None,
    transaction_id: str | None,
    input_features_json: dict,
    proba_fraud: float | None,
    review: bool,
    rank: int | None,
    is_valid: bool,
    missing_features_json: list[str] | dict | None,
) -> Prediction:
    prediction = Prediction(
        batch_job_id=batch_job_id,
        model_version_id=model_version_id,
        transaction_id=transaction_id,
        input_features_json=input_features_json,
        proba_fraud=proba_fraud,
        review=review,
        rank=rank,
        is_valid=is_valid,
        missing_features_json=missing_features_json,
    )
    db.add(prediction)
    return prediction


def list_predictions(
    db: Session,
    *,
    limit: int,
    offset: int,
    only_invalid: bool = False,
    only_review: bool = False,
    batch_job_id: int | None = None,
) -> list[Prediction]:
    stmt = select(Prediction)
    if only_invalid:
        stmt = stmt.where(Prediction.is_valid.is_(False))
    if only_review:
        stmt = stmt.where(Prediction.review.is_(True))
    if batch_job_id is not None:
        stmt = stmt.where(Prediction.batch_job_id == batch_job_id)
    stmt = stmt.order_by(desc(Prediction.created_at)).limit(limit).offset(offset)
    return list(db.scalars(stmt).all())


def list_predictions_by_batch_job(
    db: Session,
    *,
    batch_job_id: int,
    limit: int,
    offset: int,
    only_invalid: bool = False,
    only_review: bool = False,
) -> list[Prediction]:
    stmt = select(Prediction).where(Prediction.batch_job_id == batch_job_id)
    if only_invalid:
        stmt = stmt.where(Prediction.is_valid.is_(False))
    if only_review:
        stmt = stmt.where(Prediction.review.is_(True))
    stmt = stmt.order_by(desc(Prediction.created_at)).limit(limit).offset(offset)
    return list(db.scalars(stmt).all())


def get_prediction_by_id(db: Session, prediction_id: int) -> Prediction | None:
    stmt = select(Prediction).where(Prediction.id == prediction_id)
    return db.scalar(stmt)


def list_all_predictions_by_batch_job(
    db: Session,
    *,
    batch_job_id: int,
) -> list[Prediction]:
    stmt = (
        select(Prediction)
        .where(Prediction.batch_job_id == batch_job_id)
        .order_by(asc(Prediction.id))
    )
    return list(db.scalars(stmt).all())
