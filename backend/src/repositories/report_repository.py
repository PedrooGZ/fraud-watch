from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from src.db.models import Report


def create_report(
    db: Session,
    *,
    report_code: str,
    period: str,
    format: str,
    detail_level: str,
    sections_json: list | dict,
    file_path: str | None,
    generated_by_user_id: int | None = None,
) -> Report:
    report = Report(
        report_code=report_code,
        period=period,
        format=format,
        detail_level=detail_level,
        sections_json=sections_json,
        file_path=file_path,
        generated_by_user_id=generated_by_user_id,
    )
    db.add(report)
    return report


def list_reports(db: Session, *, limit: int, offset: int) -> list[Report]:
    stmt = select(Report).order_by(desc(Report.created_at)).limit(limit).offset(offset)
    return list(db.scalars(stmt).all())


def get_report_by_id(db: Session, report_id: int) -> Report | None:
    stmt = select(Report).where(Report.id == report_id)
    return db.scalar(stmt)
