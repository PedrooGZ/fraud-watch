from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from src.db.models import DriftRun


def list_drift_runs(db: Session, *, limit: int, offset: int) -> list[DriftRun]:
    stmt = select(DriftRun).order_by(desc(DriftRun.created_at)).limit(limit).offset(offset)
    return list(db.scalars(stmt).all())


def create_drift_run(
    db: Session,
    *,
    psi: float,
    status: str,
    bins: int,
    sample_size: int,
    amount_multiplier: float,
    ref_mean: float,
    ref_p95: float,
    new_mean: float,
    new_p95: float,
    summary_path: str | None = None,
) -> DriftRun:
    item = DriftRun(
        psi=psi,
        status=status,
        bins=bins,
        sample_size=sample_size,
        amount_multiplier=amount_multiplier,
        ref_mean=ref_mean,
        ref_p95=ref_p95,
        new_mean=new_mean,
        new_p95=new_p95,
        summary_path=summary_path,
    )
    db.add(item)
    return item
