from __future__ import annotations

from datetime import datetime, timezone
import logging

from sqlalchemy.exc import SQLAlchemyError

from src.db.session import SessionLocal
from src.repositories.batch_job_repository import create_batch_job, finalize_batch_job
from src.repositories.model_repository import get_active_model_version
from src.repositories.prediction_repository import create_prediction
from src.services.audit_service import write_audit_event_best_effort

logger = logging.getLogger(__name__)


def persist_single_prediction(
    *,
    input_features_json: dict,
    proba_fraud: float,
    review: int | bool,
    transaction_id: str | None = None,
) -> None:
    try:
        with SessionLocal() as db:
            active_model = get_active_model_version(db)
            model_version_id = active_model.id if active_model is not None else None

            prediction = create_prediction(
                db,
                batch_job_id=None,
                model_version_id=model_version_id,
                transaction_id=transaction_id,
                input_features_json=input_features_json,
                proba_fraud=proba_fraud,
                review=bool(review),
                rank=None,
                is_valid=True,
                missing_features_json=None,
            )
            db.flush()
            db.commit()

            write_audit_event_best_effort(
                event_type="PREDICTION_CREATED",
                entity_type="prediction",
                entity_id=str(prediction.id),
                details_json={
                    "proba_fraud": proba_fraud,
                    "review": bool(review),
                    "source": "single",
                },
                user_id=None,
            )
    except SQLAlchemyError as exc:
        try:
            db.rollback()
        except Exception:
            pass
        logger.warning("No se pudo persistir prediccion individual en DB: %s", exc)
    except Exception as exc:
        try:
            db.rollback()
        except Exception:
            pass
        logger.warning("Error inesperado al persistir prediccion individual: %s", exc)


def persist_batch_predictions(
    *,
    transactions: list[dict[str, float]],
    results_valid: list[dict],
    results_invalid: list[dict],
    total_rows: int,
    valid_rows: int,
    invalid_rows: int,
    review_count: int,
    filename: str = "api_batch",
) -> None:
    try:
        with SessionLocal() as db:
            active_model = get_active_model_version(db)
            model_version_id = active_model.id if active_model is not None else None

            batch_job = create_batch_job(
                db,
                filename=filename,
                status="processing",
                total_rows=total_rows,
                valid_rows=valid_rows,
                invalid_rows=invalid_rows,
                review_count=review_count,
            )
            db.flush()

            for item in results_valid:
                original_index = int(item["index"])
                create_prediction(
                    db,
                    batch_job_id=batch_job.id,
                    model_version_id=model_version_id,
                    transaction_id=None,
                    input_features_json=transactions[original_index],
                    proba_fraud=float(item["proba_fraud"]),
                    review=bool(item["review"]),
                    rank=(int(item["rank"]) if item.get("rank") is not None else None),
                    is_valid=True,
                    missing_features_json=None,
                )

            for item in results_invalid:
                original_index = int(item["index"])
                create_prediction(
                    db,
                    batch_job_id=batch_job.id,
                    model_version_id=model_version_id,
                    transaction_id=None,
                    input_features_json=transactions[original_index],
                    proba_fraud=None,
                    review=False,
                    rank=None,
                    is_valid=False,
                    missing_features_json=item.get("missing_features", []),
                )

            finalize_batch_job(
                batch_job,
                status="completed",
                total_rows=total_rows,
                valid_rows=valid_rows,
                invalid_rows=invalid_rows,
                review_count=review_count,
                finished_at=datetime.now(timezone.utc),
            )
            db.commit()

            write_audit_event_best_effort(
                event_type="BATCH_COMPLETED",
                entity_type="batch_job",
                entity_id=str(batch_job.id),
                details_json={
                    "total_rows": total_rows,
                    "valid_rows": valid_rows,
                    "invalid_rows": invalid_rows,
                    "review_count": review_count,
                },
                user_id=None,
            )
    except SQLAlchemyError as exc:
        try:
            db.rollback()
        except Exception:
            pass
        logger.warning("No se pudo persistir batch en DB: %s", exc)
    except Exception as exc:
        try:
            db.rollback()
        except Exception:
            pass
        logger.warning("Error inesperado al persistir batch en DB: %s", exc)
