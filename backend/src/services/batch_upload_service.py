from __future__ import annotations

from datetime import datetime, timezone
import io
import logging
from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from src.db.session import SessionLocal
from src.repositories.audit_repository import create_audit_event
from src.repositories.batch_job_repository import create_batch_job, finalize_batch_job
from src.repositories.model_repository import get_active_model_version
from src.repositories.prediction_repository import create_prediction
from src.services.drift_service import try_create_drift_run_for_scores

logger = logging.getLogger(__name__)


def _to_python_scalar(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, np.generic):
        return value.item()
    return value


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return bool(pd.isna(value))


def parse_and_score_csv_batch(
    *,
    file_bytes: bytes,
    model,
    feature_cols: list[str],
    threshold: float,
    max_alerts: int,
    preview_limit: int = 20,
) -> dict:
    if not file_bytes:
        raise ValueError("El CSV está vacío.")

    try:
        dataframe = pd.read_csv(io.BytesIO(file_bytes))
    except Exception as exc:
        raise ValueError("No se pudo parsear el CSV.") from exc

    if dataframe.empty:
        raise ValueError("El CSV está vacío.")

    available_columns = set(dataframe.columns)

    transactions_payload: list[dict] = []
    valid_entries: list[dict] = []
    invalid_entries: list[dict] = []

    for index, row in dataframe.iterrows():
        row_payload = {column: _to_python_scalar(value) for column, value in row.to_dict().items()}
        transactions_payload.append(row_payload)

        missing_features: list[str] = []
        invalid_value_features: list[str] = []
        valid_features: dict[str, float] = {}

        for column in feature_cols:
            if column not in available_columns:
                missing_features.append(column)
                continue

            raw_value = row[column]
            if _is_blank(raw_value):
                missing_features.append(column)
                continue

            try:
                valid_features[column] = float(raw_value)
            except Exception:
                invalid_value_features.append(column)

        if missing_features or invalid_value_features:
            merged_errors = sorted(set(missing_features + invalid_value_features))
            invalid_entries.append(
                {
                    "index": int(index),
                    "missing_features": merged_errors,
                }
            )
            continue

        valid_entries.append(
            {
                "index": int(index),
                "features": valid_features,
            }
        )

    valid_results: list[dict] = []
    if valid_entries:
        x_values = np.array(
            [[entry["features"][column] for column in feature_cols] for entry in valid_entries],
            dtype=float,
        )
        probs = model.predict_proba(x_values)[:, 1].astype(float)

        candidates_mask = probs >= threshold
        candidate_indices = np.where(candidates_mask)[0]
        n_candidates = int(candidates_mask.sum())

        review_mask = np.zeros(len(valid_entries), dtype=bool)
        rank_values = np.full(len(valid_entries), -1, dtype=int)

        ordered_candidates = candidate_indices[np.argsort(-probs[candidate_indices])]
        if n_candidates <= max_alerts:
            selected_indices = ordered_candidates
        else:
            selected_indices = ordered_candidates[:max_alerts]

        review_mask[selected_indices] = True
        for position, idx in enumerate(selected_indices, start=1):
            rank_values[idx] = position

        for row_index, entry in enumerate(valid_entries):
            review = bool(review_mask[row_index])
            rank = int(rank_values[row_index]) if review else None
            valid_results.append(
                {
                    "index": entry["index"],
                    "proba_fraud": float(probs[row_index]),
                    "review": review,
                    "rank": rank,
                }
            )

    review_count = sum(1 for item in valid_results if item["review"])
    total_rows = len(transactions_payload)
    valid_rows = len(valid_results)
    invalid_rows = len(invalid_entries)

    preview: list[dict] = []
    for item in valid_results:
        preview.append(
            {
                "index": item["index"],
                "proba_fraud": item["proba_fraud"],
                "review": item["review"],
                "rank": item["rank"],
                "is_valid": True,
                "missing_features": None,
            }
        )
    for item in invalid_entries:
        preview.append(
            {
                "index": item["index"],
                "proba_fraud": None,
                "review": False,
                "rank": None,
                "is_valid": False,
                "missing_features": item["missing_features"],
            }
        )
    preview = sorted(preview, key=lambda item: item["index"])[:preview_limit]

    return {
        "transactions": transactions_payload,
        "results_valid": valid_results,
        "results_invalid": invalid_entries,
        "total_rows": total_rows,
        "valid_rows": valid_rows,
        "invalid_rows": invalid_rows,
        "review_count": review_count,
        "results_preview": preview,
    }


def persist_uploaded_batch(
    *,
    filename: str,
    scored_batch: dict,
) -> int:
    with SessionLocal() as db:
        return _persist_uploaded_batch_tx(db=db, filename=filename, scored_batch=scored_batch)


def _persist_uploaded_batch_tx(
    *,
    db: Session,
    filename: str,
    scored_batch: dict,
) -> int:
    active_model = get_active_model_version(db)
    model_version_id = active_model.id if active_model is not None else None

    batch_job = create_batch_job(
        db,
        filename=filename,
        status="processing",
        total_rows=scored_batch["total_rows"],
        valid_rows=scored_batch["valid_rows"],
        invalid_rows=scored_batch["invalid_rows"],
        review_count=scored_batch["review_count"],
    )
    db.flush()

    transactions = scored_batch["transactions"]

    for item in scored_batch["results_valid"]:
        source_index = int(item["index"])
        create_prediction(
            db,
            batch_job_id=batch_job.id,
            model_version_id=model_version_id,
            transaction_id=None,
            input_features_json=transactions[source_index],
            proba_fraud=float(item["proba_fraud"]),
            review=bool(item["review"]),
            rank=item["rank"],
            is_valid=True,
            missing_features_json=None,
        )

    for item in scored_batch["results_invalid"]:
        source_index = int(item["index"])
        create_prediction(
            db,
            batch_job_id=batch_job.id,
            model_version_id=model_version_id,
            transaction_id=None,
            input_features_json=transactions[source_index],
            proba_fraud=None,
            review=False,
            rank=None,
            is_valid=False,
            missing_features_json=item.get("missing_features", []),
        )

    new_scores = [
        float(item["proba_fraud"])
        for item in scored_batch["results_valid"]
        if item.get("proba_fraud") is not None
    ]
    drift_run = None
    try:
        drift_run = try_create_drift_run_for_scores(
            db,
            new_scores=new_scores,
            batch_job_id=batch_job.id,
        )
        if drift_run is not None:
            db.flush()
    except Exception:
        logger.exception("Failed to create drift run for uploaded batch")

    finalize_batch_job(
        batch_job,
        status="completed",
        total_rows=scored_batch["total_rows"],
        valid_rows=scored_batch["valid_rows"],
        invalid_rows=scored_batch["invalid_rows"],
        review_count=scored_batch["review_count"],
        finished_at=datetime.now(timezone.utc),
    )

    create_audit_event(
        db,
        user_id=None,
        event_type="BATCH_UPLOADED",
        entity_type="batch_job",
        entity_id=str(batch_job.id),
        details_json={
            "total_rows": scored_batch["total_rows"],
            "valid_rows": scored_batch["valid_rows"],
            "invalid_rows": scored_batch["invalid_rows"],
            "review_count": scored_batch["review_count"],
            "filename": filename,
            "drift_run_id": drift_run.id if drift_run is not None else None,
        },
    )

    db.commit()
    return batch_job.id


