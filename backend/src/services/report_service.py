from __future__ import annotations

import csv
from datetime import date, datetime, timezone
import json
import logging
from pathlib import Path

from sqlalchemy.orm import Session

from src.core.config import DATA_DIR
from src.repositories.audit_repository import create_audit_event, list_audit_events
from src.repositories.batch_job_repository import list_batch_jobs
from src.repositories.drift_repository import list_drift_runs
from src.repositories.model_repository import get_active_model_version
from src.repositories.policy_repository import list_policy_history
from src.repositories.report_repository import create_report
from src.schemas.report_schema import ReportCreateRequest
from src.services.analytics_service import (
    get_analytics_classification_summary,
    get_analytics_fraud_evolution,
    get_analytics_risk_distribution,
    get_analytics_variable_importance,
)
from src.services.dashboard_service import get_dashboard_summary

logger = logging.getLogger(__name__)

REPORTS_DIR = DATA_DIR / "reports"
PERIOD_TO_DAYS = {
    "today": 1,
    "last_7_days": 7,
    "last_30_days": 30,
    "all": 3650,
}


def generate_report_code() -> str:
    now = datetime.now(timezone.utc)
    return f"FW-{now.strftime('%Y%m%d-%H%M%S')}-{now.strftime('%f')}"


def _to_iso(value):
    return value.isoformat() if hasattr(value, "isoformat") else value


def _serialize_model(model) -> dict | None:
    if model is None:
        return None
    return {
        "id": model.id,
        "name": model.name,
        "model_type": model.model_type,
        "artifact_path": model.artifact_path,
        "metadata_path": model.metadata_path,
        "pr_auc": float(model.pr_auc),
        "brier_score": float(model.brier_score),
        "n_features": int(model.n_features),
        "is_active": bool(model.is_active),
        "created_at": _to_iso(model.created_at),
    }


def _serialize_drift_run(item) -> dict:
    return {
        "id": item.id,
        "psi": float(item.psi),
        "status": item.status,
        "bins": int(item.bins),
        "sample_size": int(item.sample_size),
        "amount_multiplier": float(item.amount_multiplier),
        "ref_mean": float(item.ref_mean),
        "ref_p95": float(item.ref_p95),
        "new_mean": float(item.new_mean),
        "new_p95": float(item.new_p95),
        "summary_path": item.summary_path,
        "created_at": _to_iso(item.created_at),
    }


def _serialize_policy_history(item) -> dict:
    return {
        "id": item.id,
        "policy_id": item.policy_id,
        "changed_by_user_id": item.changed_by_user_id,
        "old_values_json": item.old_values_json,
        "new_values_json": item.new_values_json,
        "reason": item.reason,
        "created_at": _to_iso(item.created_at),
    }


def _serialize_audit_event(item) -> dict:
    return {
        "id": item.id,
        "user_id": item.user_id,
        "event_type": item.event_type,
        "entity_type": item.entity_type,
        "entity_id": item.entity_id,
        "details_json": item.details_json,
        "created_at": _to_iso(item.created_at),
    }


def _serialize_batch_job(item) -> dict:
    return {
        "id": item.id,
        "filename": item.filename,
        "status": item.status,
        "total_rows": int(item.total_rows),
        "valid_rows": int(item.valid_rows),
        "invalid_rows": int(item.invalid_rows),
        "review_count": int(item.review_count),
        "error_message": item.error_message,
        "created_at": _to_iso(item.created_at),
        "finished_at": _to_iso(item.finished_at),
    }


def build_report_payload(db: Session, request: ReportCreateRequest, report_code: str) -> dict:
    sections_payload: dict = {}
    days = PERIOD_TO_DAYS.get(request.period, 30)

    for section in request.sections:
        if section == "summary":
            sections_payload["summary"] = get_dashboard_summary(db)
        elif section == "analytics":
            sections_payload["analytics"] = {
                "fraud_evolution": get_analytics_fraud_evolution(db, days=days),
                "risk_distribution": get_analytics_risk_distribution(db),
                "classification_summary": get_analytics_classification_summary(db),
                "variable_importance": get_analytics_variable_importance(limit=10),
            }
        elif section == "drift":
            drift_items = list_drift_runs(db, limit=1, offset=0)
            sections_payload["drift"] = [_serialize_drift_run(item) for item in drift_items]
        elif section == "model":
            sections_payload["model"] = _serialize_model(get_active_model_version(db))
        elif section == "policy_changes":
            history_items = list_policy_history(db, limit=10, offset=0)
            sections_payload["policy_changes"] = [
                _serialize_policy_history(item) for item in history_items
            ]
        elif section == "audit":
            audit_items = list_audit_events(db, limit=10, offset=0)
            sections_payload["audit"] = [_serialize_audit_event(item) for item in audit_items]
        elif section == "batch_jobs":
            batch_items = list_batch_jobs(db, limit=10, offset=0)
            sections_payload["batch_jobs"] = [_serialize_batch_job(item) for item in batch_items]

    return {
        "report_code": report_code,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "period": request.period,
        "format": request.format,
        "detail_level": request.detail_level,
        "sections": sections_payload,
    }


def create_report_file(report_code: str, payload: dict) -> Path:
    def _json_default(value):
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        return str(value)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = REPORTS_DIR / f"{report_code}.json"
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default),
        encoding="utf-8",
    )
    return output_path


def _stringify_value(value) -> str:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    if value is None:
        return ""
    return str(value)


def _flatten_section_rows(section_name: str, value, rows: list[list[str]]) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if isinstance(nested, (dict, list)):
                _flatten_section_rows(section_name, nested, rows)
            else:
                rows.append([section_name, str(key), _stringify_value(nested)])
        return

    if isinstance(value, list):
        for index, item in enumerate(value):
            if isinstance(item, dict):
                for key, nested in item.items():
                    rows.append([section_name, f"{section_name}.{index}.{key}", _stringify_value(nested)])
            elif isinstance(item, list):
                rows.append([section_name, f"{section_name}.{index}", _stringify_value(item)])
            else:
                rows.append([section_name, f"{section_name}.{index}", _stringify_value(item)])
        return

    rows.append([section_name, section_name, _stringify_value(value)])


def create_report_csv_file(report_code: str, payload: dict) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = REPORTS_DIR / f"{report_code}.csv"

    rows: list[list[str]] = [
        ["metadata", "report_code", _stringify_value(payload.get("report_code"))],
        ["metadata", "generated_at", _stringify_value(payload.get("generated_at"))],
        ["metadata", "period", _stringify_value(payload.get("period"))],
        ["metadata", "detail_level", _stringify_value(payload.get("detail_level"))],
        ["metadata", "format", _stringify_value(payload.get("format"))],
    ]

    sections = payload.get("sections", {})
    if isinstance(sections, dict):
        for section_name, section_value in sections.items():
            _flatten_section_rows(section_name, section_value, rows)

    with output_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["section", "key", "value"])
        writer.writerows(rows)

    return output_path


def create_report_output_file(report_code: str, payload: dict, report_format: str) -> Path:
    if report_format == "json":
        return create_report_file(report_code, payload)
    if report_format == "csv":
        return create_report_csv_file(report_code, payload)
    raise ValueError(f"Unsupported report format: {report_format}")


def create_report_from_request(db: Session, request: ReportCreateRequest):
    report_code = generate_report_code()
    payload = build_report_payload(db, request, report_code)
    file_path = create_report_output_file(report_code, payload, request.format)

    report = create_report(
        db,
        report_code=report_code,
        period=request.period,
        format=request.format,
        detail_level=request.detail_level,
        sections_json=request.sections,
        file_path=str(file_path),
        generated_by_user_id=None,
    )
    db.flush()

    try:
        create_audit_event(
            db,
            user_id=None,
            event_type="REPORT_CREATED",
            entity_type="report",
            entity_id=str(report.id),
            details_json={
                "report_code": report.report_code,
                "period": report.period,
                "format": report.format,
                "detail_level": report.detail_level,
                "sections": request.sections,
            },
        )
    except Exception as exc:
        logger.warning("Could not register REPORT_CREATED audit event: %s", exc)

    return report
