from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from src.db.models import ModelVersion


def get_active_model_version(db: Session) -> ModelVersion | None:
    stmt = (
        select(ModelVersion)
        .where(ModelVersion.is_active.is_(True))
        .order_by(ModelVersion.created_at.desc())
    )
    return db.scalar(stmt)


def list_model_versions(
    db: Session,
    *,
    limit: int,
    offset: int,
    only_active: bool = False,
) -> list[ModelVersion]:
    stmt = select(ModelVersion)
    if only_active:
        stmt = stmt.where(ModelVersion.is_active.is_(True))
    stmt = stmt.order_by(desc(ModelVersion.created_at)).limit(limit).offset(offset)
    return list(db.scalars(stmt).all())
