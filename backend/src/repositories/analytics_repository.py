from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, case, func, select
from sqlalchemy.orm import Session

from src.db.models import Prediction


def list_fraud_evolution_by_day(db: Session, *, days: int) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    day_expr = func.date(Prediction.created_at)
    stmt = (
        select(
            day_expr.label("date"),
            func.count(Prediction.id).label("total_predictions"),
            func.sum(case((Prediction.review.is_(True), 1), else_=0)).label("review_count"),
            func.sum(case((Prediction.is_valid.is_(False), 1), else_=0)).label("invalid_count"),
        )
        .where(Prediction.created_at >= cutoff)
        .group_by(day_expr)
        .order_by(day_expr.asc())
    )

    rows = db.execute(stmt).all()
    return [
        {
            "date": row.date,
            "total_predictions": int(row.total_predictions or 0),
            "review_count": int(row.review_count or 0),
            "invalid_count": int(row.invalid_count or 0),
        }
        for row in rows
    ]


def get_risk_distribution_counts(
    db: Session,
    *,
    policy_threshold: float,
    high_threshold: float,
) -> dict:
    valid_with_proba = and_(Prediction.is_valid.is_(True), Prediction.proba_fraud.is_not(None))

    stmt = select(
        func.sum(case((Prediction.proba_fraud < policy_threshold, 1), else_=0)).label("low"),
        func.sum(
            case(
                (
                    and_(
                        Prediction.proba_fraud >= policy_threshold,
                        Prediction.proba_fraud < high_threshold,
                    ),
                    1,
                ),
                else_=0,
            )
        ).label("medium"),
        func.sum(case((Prediction.proba_fraud >= high_threshold, 1), else_=0)).label("high"),
        func.count(Prediction.id).label("total"),
    ).where(valid_with_proba)

    row = db.execute(stmt).one()
    return {
        "low": int(row.low or 0),
        "medium": int(row.medium or 0),
        "high": int(row.high or 0),
        "total": int(row.total or 0),
    }


def get_classification_summary_counts(db: Session) -> dict:
    stmt = select(
        func.sum(case((and_(Prediction.is_valid.is_(True), Prediction.review.is_(True)), 1), else_=0)).label("review"),
        func.sum(
            case((and_(Prediction.is_valid.is_(True), Prediction.review.is_(False)), 1), else_=0)
        ).label("no_review"),
        func.sum(case((Prediction.is_valid.is_(False), 1), else_=0)).label("invalid"),
        func.count(Prediction.id).label("total"),
    )

    row = db.execute(stmt).one()
    return {
        "review": int(row.review or 0),
        "no_review": int(row.no_review or 0),
        "invalid": int(row.invalid or 0),
        "total": int(row.total or 0),
    }
