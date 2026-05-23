from __future__ import annotations

from datetime import datetime, timezone
import csv
import io
import json
import logging
import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, HTTPException, Query, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer
import joblib
import numpy as np
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError

from src.core.config import (
    BACKEND_DIR,
    DATA_DIR,
    MODEL_METADATA_PATH as DEFAULT_META_PATH,
    MODEL_PATH as DEFAULT_MODEL_PATH,
    PREDICTIONS_LOG_PATH as DEFAULT_LOG_PATH,
    REVIEW_POLICY_PATH as DEFAULT_POLICY_PATH,
)
from src.db.session import SessionLocal
from src.repositories.audit_repository import list_audit_events
from src.repositories.batch_job_repository import get_batch_job_by_id, list_batch_jobs
from src.repositories.drift_repository import list_drift_runs
from src.repositories.model_repository import get_active_model_version, list_model_versions
from src.repositories.policy_repository import list_policy_history
from src.repositories.prediction_repository import (
    get_prediction_by_id,
    list_all_predictions_by_batch_job,
    list_predictions,
    list_predictions_by_batch_job,
)
from src.repositories.report_repository import get_report_by_id, list_reports
from src.schemas.audit_schema import AuditEventResponse
from src.schemas.auth_schema import LoginRequest, RegisterRequest, TokenResponse
from src.schemas.analytics_schema import (
    AnalyticsClassificationSummaryResponse,
    AnalyticsFraudEvolutionResponse,
    AnalyticsRiskDistributionResponse,
    AnalyticsVariableImportanceResponse,
)
from src.schemas.batch_schema import BatchJobResponse, BatchUploadResponse
from src.schemas.dashboard_schema import (
    DashboardPriorityCaseResponse,
    DashboardSummaryResponse,
)
from src.schemas.drift_schema import DriftRunResponse
from src.schemas.model_schema import ModelVersionResponse
from src.schemas.policy_schema import (
    PolicyHistoryResponse,
    PolicyUpdateRequest,
)
from src.schemas.prediction_schema import (
    PredictionDetailResponse,
    PredictionSummaryResponse,
)
from src.schemas.report_schema import ReportCreateRequest, ReportResponse
from src.schemas.user_schema import UserResponse
from src.services.policy_service import (
    get_policy_with_fallback,
    update_active_policy,
)
from src.services.batch_upload_service import (
    parse_and_score_csv_batch,
    persist_uploaded_batch,
)
from src.services.analytics_service import (
    get_analytics_classification_summary,
    get_analytics_fraud_evolution,
    get_analytics_risk_distribution,
    get_analytics_variable_importance,
)
from src.services.dashboard_service import (
    get_dashboard_priority_cases,
    get_dashboard_summary,
)
from src.services.report_service import create_report_from_request
from src.services.prediction_persistence_service import (
    persist_batch_predictions,
    persist_single_prediction,
)
from src.services.audit_service import write_audit_event_best_effort
from src.services.auth_service import (
    authenticate_user,
    create_access_token,
    get_current_user_from_token,
    register_user,
)

load_dotenv()
logger = logging.getLogger(__name__)

MODEL_PATH = Path(os.getenv("MODEL_PATH", str(DEFAULT_MODEL_PATH)))
META_PATH = Path(os.getenv("MODEL_METADATA_PATH", str(DEFAULT_META_PATH)))
LOG_PATH = Path(os.getenv("PREDICTIONS_LOG_PATH", str(DEFAULT_LOG_PATH)))
POLICY_PATH = Path(os.getenv("REVIEW_POLICY_PATH", str(DEFAULT_POLICY_PATH)))

app = FastAPI(title="Fraud Scoring API", version="1.3.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost",
        "http://localhost:80",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_bundle = None
REPORTS_BASE_DIR = (DATA_DIR / "reports").resolve()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_bundle():
    global _bundle
    if _bundle is None:
        if not MODEL_PATH.exists():
            raise RuntimeError(f"No existe {MODEL_PATH}. Ejecuta train_final_model primero.")
        _bundle = joblib.load(MODEL_PATH)
    return _bundle


def append_log(record: dict) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_policy() -> dict:
    return get_policy_with_fallback(POLICY_PATH)


def _run_db_read(operation_name: str, callback):
    try:
        with SessionLocal() as db:
            return callback(db)
    except SQLAlchemyError as exc:
        logger.exception("Database error in %s: %s", operation_name, exc)
        raise HTTPException(status_code=503, detail="Database unavailable.")
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected database error in %s: %s", operation_name, exc)
        raise HTTPException(status_code=503, detail="Database unavailable.")


def _serialize_batch_job(job) -> BatchJobResponse:
    return BatchJobResponse(
        id=job.id,
        filename=job.filename,
        status=job.status,
        total_rows=job.total_rows,
        valid_rows=job.valid_rows,
        invalid_rows=job.invalid_rows,
        review_count=job.review_count,
        error_message=job.error_message,
        created_at=job.created_at,
        finished_at=job.finished_at,
    )


def _serialize_prediction_summary(prediction) -> PredictionSummaryResponse:
    return PredictionSummaryResponse(
        id=prediction.id,
        batch_job_id=prediction.batch_job_id,
        model_version_id=prediction.model_version_id,
        transaction_id=prediction.transaction_id,
        proba_fraud=prediction.proba_fraud,
        review=bool(prediction.review),
        rank=prediction.rank,
        is_valid=bool(prediction.is_valid),
        missing_features_json=prediction.missing_features_json,
        created_at=prediction.created_at,
    )


def _serialize_prediction_detail(prediction) -> PredictionDetailResponse:
    return PredictionDetailResponse(
        id=prediction.id,
        batch_job_id=prediction.batch_job_id,
        model_version_id=prediction.model_version_id,
        transaction_id=prediction.transaction_id,
        input_features_json=prediction.input_features_json,
        proba_fraud=prediction.proba_fraud,
        review=bool(prediction.review),
        rank=prediction.rank,
        is_valid=bool(prediction.is_valid),
        missing_features_json=prediction.missing_features_json,
        created_at=prediction.created_at,
    )


def _serialize_policy_history(item) -> PolicyHistoryResponse:
    return PolicyHistoryResponse(
        id=item.id,
        policy_id=item.policy_id,
        changed_by_user_id=item.changed_by_user_id,
        old_values_json=item.old_values_json,
        new_values_json=item.new_values_json,
        reason=item.reason,
        created_at=item.created_at,
    )


def _serialize_audit_event(item) -> AuditEventResponse:
    return AuditEventResponse(
        id=item.id,
        user_id=item.user_id,
        event_type=item.event_type,
        entity_type=item.entity_type,
        entity_id=item.entity_id,
        details_json=item.details_json,
        created_at=item.created_at,
    )


def _serialize_model_version(item) -> ModelVersionResponse:
    return ModelVersionResponse(
        id=item.id,
        name=item.name,
        model_type=item.model_type,
        artifact_path=item.artifact_path,
        metadata_path=item.metadata_path,
        pr_auc=item.pr_auc,
        brier_score=item.brier_score,
        n_features=item.n_features,
        is_active=bool(item.is_active),
        created_at=item.created_at,
    )


def _serialize_report(item) -> ReportResponse:
    return ReportResponse(
        id=item.id,
        report_code=item.report_code,
        period=item.period,
        format=item.format,
        detail_level=item.detail_level,
        sections_json=item.sections_json,
        file_path=item.file_path,
        generated_by_user_id=item.generated_by_user_id,
        created_at=item.created_at,
    )


def _resolve_report_download_path(file_path: str | None) -> Path:
    if not file_path:
        raise HTTPException(status_code=404, detail="Report file not found.")

    raw_path = Path(file_path)
    resolved = (BACKEND_DIR / raw_path).resolve() if not raw_path.is_absolute() else raw_path.resolve()

    try:
        resolved.relative_to(REPORTS_BASE_DIR)
    except ValueError:
        raise HTTPException(status_code=404, detail="Report file not found.")

    if not resolved.exists() or not resolved.is_file():
        raise HTTPException(status_code=404, detail="Report file not found.")

    return resolved


def _serialize_drift_run(item) -> DriftRunResponse:
    return DriftRunResponse(
        id=item.id,
        psi=item.psi,
        status=item.status,
        bins=item.bins,
        sample_size=item.sample_size,
        amount_multiplier=item.amount_multiplier,
        ref_mean=item.ref_mean,
        ref_p95=item.ref_p95,
        new_mean=item.new_mean,
        new_p95=item.new_p95,
        summary_path=item.summary_path,
        created_at=item.created_at,
    )


def _serialize_user(item) -> UserResponse:
    return UserResponse(
        id=item.id,
        email=item.email,
        full_name=item.full_name,
        role=item.role,
        is_active=bool(item.is_active),
        created_at=item.created_at,
    )


def _serialize_dashboard_priority_case(item: dict) -> DashboardPriorityCaseResponse:
    return DashboardPriorityCaseResponse(
        id=item["id"],
        batch_job_id=item.get("batch_job_id"),
        model_version_id=item.get("model_version_id"),
        transaction_id=item.get("transaction_id"),
        proba_fraud=item.get("proba_fraud"),
        review=bool(item.get("review", False)),
        rank=item.get("rank"),
        is_valid=bool(item.get("is_valid", False)),
        created_at=item["created_at"],
    )


def _get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        with SessionLocal() as db:
            return get_current_user_from_token(db, token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    except SQLAlchemyError as exc:
        logger.exception("Database error fetching current user: %s", exc)
        raise HTTPException(status_code=503, detail="Database unavailable.")
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error fetching current user: %s", exc)
        raise HTTPException(status_code=503, detail="Database unavailable.")


def _get_current_admin_user(current_user=Depends(_get_current_user)):
    if str(getattr(current_user, "role", "")).lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin role required.")
    return current_user


class Transaction(BaseModel):
    features: dict[str, float] = Field(..., description="Features numericas (V1..V28, Amount)")


class PredictionResponse(BaseModel):
    proba_fraud: float
    review: int
    threshold_cost: float


class BatchRequest(BaseModel):
    transactions: list[Transaction]


class BatchItemValid(BaseModel):
    index: int
    proba_fraud: float
    review: int
    rank: int | None = None


class BatchItemInvalid(BaseModel):
    index: int
    missing_features: list[str]


class BatchResponse(BaseModel):
    threshold_cost: float
    max_alerts: int

    n_total: int
    n_valid: int
    n_invalid: int

    n_candidates: int
    n_review: int

    results_valid: list[BatchItemValid]
    results_invalid: list[BatchItemInvalid]


CSV_ALLOWED_CONTENT_TYPES = {
    "text/csv",
    "application/csv",
    "application/vnd.ms-excel",
}


@app.get("/health")
def health():
    meta = {}
    if META_PATH.exists():
        try:
            meta = json.loads(META_PATH.read_text(encoding="utf-8"))
        except Exception:
            meta = {}

    return {
        "status": "ok",
        "timestamp": now_utc(),
        "model_file_exists": MODEL_PATH.exists(),
        "holdout_metrics": meta.get("holdout_metrics", {}),
        "model_type": meta.get("model_type", "unknown"),
        "n_features": meta.get("n_features", None),
        "policy": load_policy(),
    }


@app.post("/auth/register", response_model=TokenResponse)
def auth_register(payload: RegisterRequest):
    try:
        with SessionLocal() as db:
            user = register_user(db, payload)
            db.commit()
            db.refresh(user)

            token = create_access_token(subject=user.id)
            return TokenResponse(
                access_token=token,
                token_type="bearer",
                user=_serialize_user(user),
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except SQLAlchemyError as exc:
        logger.exception("Database error registering user: %s", exc)
        raise HTTPException(status_code=503, detail="Database unavailable.")
    except Exception as exc:
        logger.exception("Unexpected error registering user: %s", exc)
        raise HTTPException(status_code=503, detail="Database unavailable.")


@app.post("/auth/login", response_model=TokenResponse)
def auth_login(payload: LoginRequest):
    try:
        with SessionLocal() as db:
            user = authenticate_user(db, str(payload.email), payload.password)
            if user is None:
                raise HTTPException(status_code=401, detail="Invalid credentials.")

            token = create_access_token(subject=user.id)
            return TokenResponse(
                access_token=token,
                token_type="bearer",
                user=_serialize_user(user),
            )
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        logger.exception("Database error logging in user: %s", exc)
        raise HTTPException(status_code=503, detail="Database unavailable.")
    except Exception as exc:
        logger.exception("Unexpected error logging in user: %s", exc)
        raise HTTPException(status_code=503, detail="Database unavailable.")


@app.get("/auth/me", response_model=UserResponse)
def auth_me(token: str = Depends(oauth2_scheme)):
    try:
        with SessionLocal() as db:
            user = get_current_user_from_token(db, token)
            return _serialize_user(user)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    except SQLAlchemyError as exc:
        logger.exception("Database error fetching current user: %s", exc)
        raise HTTPException(status_code=503, detail="Database unavailable.")
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error fetching current user: %s", exc)
        raise HTTPException(status_code=503, detail="Database unavailable.")


@app.get("/policy")
def policy():
    return {"timestamp": now_utc(), "policy": load_policy(), "policy_file_exists": POLICY_PATH.exists()}


@app.put("/policy")
def update_policy(
    payload: PolicyUpdateRequest,
    current_user=Depends(_get_current_admin_user),
):
    _ = current_user
    try:
        updated_policy = update_active_policy(
            threshold_cost=payload.threshold_cost,
            max_alerts=payload.max_alerts,
            priority_mode=payload.priority_mode,
            error_cost_mode=payload.error_cost_mode,
            reason=payload.reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except SQLAlchemyError as exc:
        logger.exception("Database error updating policy: %s", exc)
        raise HTTPException(status_code=503, detail="Database unavailable.")
    except Exception as exc:
        logger.exception("Unexpected error updating policy: %s", exc)
        raise HTTPException(status_code=503, detail="Database unavailable.")

    return {
        "timestamp": now_utc(),
        "policy": updated_policy,
        "policy_file_exists": POLICY_PATH.exists(),
    }


@app.get("/policy/history", response_model=list[PolicyHistoryResponse])
def policy_history(
    limit: int = Query(20, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    return _run_db_read(
        "GET /policy/history",
        lambda db: [_serialize_policy_history(item) for item in list_policy_history(db, limit=limit, offset=offset)],
    )


@app.get("/dashboard/summary", response_model=DashboardSummaryResponse)
def dashboard_summary():
    return _run_db_read(
        "GET /dashboard/summary",
        lambda db: DashboardSummaryResponse(**get_dashboard_summary(db)),
    )


@app.get("/dashboard/priority-cases", response_model=list[DashboardPriorityCaseResponse])
def dashboard_priority_cases(
    limit: int = Query(10, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    only_review: bool = False,
):
    return _run_db_read(
        "GET /dashboard/priority-cases",
        lambda db: [
            _serialize_dashboard_priority_case(item)
            for item in get_dashboard_priority_cases(
                db,
                limit=limit,
                offset=offset,
                only_review=only_review,
            )
        ],
    )


@app.get("/analytics/fraud-evolution", response_model=AnalyticsFraudEvolutionResponse)
def analytics_fraud_evolution(days: int = Query(30, ge=1, le=3650)):
    return _run_db_read(
        "GET /analytics/fraud-evolution",
        lambda db: AnalyticsFraudEvolutionResponse(**get_analytics_fraud_evolution(db, days=days)),
    )


@app.get("/analytics/risk-distribution", response_model=AnalyticsRiskDistributionResponse)
def analytics_risk_distribution():
    return _run_db_read(
        "GET /analytics/risk-distribution",
        lambda db: AnalyticsRiskDistributionResponse(**get_analytics_risk_distribution(db)),
    )


@app.get("/analytics/classification-summary", response_model=AnalyticsClassificationSummaryResponse)
def analytics_classification_summary():
    return _run_db_read(
        "GET /analytics/classification-summary",
        lambda db: AnalyticsClassificationSummaryResponse(**get_analytics_classification_summary(db)),
    )


@app.get("/analytics/variable-importance", response_model=AnalyticsVariableImportanceResponse)
def analytics_variable_importance(limit: int = Query(10, ge=1, le=100)):
    return AnalyticsVariableImportanceResponse(**get_analytics_variable_importance(limit=limit))


def tx_to_vector_strict(tx_features: dict[str, float], feature_cols: list[str]) -> np.ndarray:
    missing = [c for c in feature_cols if c not in tx_features]
    if missing:
        raise HTTPException(status_code=400, detail=f"Faltan features requeridas: {missing}")
    return np.array([float(tx_features[c]) for c in feature_cols], dtype=float)


@app.post("/predict", response_model=PredictionResponse)
def predict(tx: Transaction):
    try:
        bundle = load_bundle()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    model = bundle["model"]
    feature_cols = bundle["feature_cols"]
    policy = load_policy()
    threshold = policy["threshold_cost"]

    x = tx_to_vector_strict(tx.features, feature_cols).reshape(1, -1)
    proba = float(model.predict_proba(x)[:, 1][0])
    review = int(proba >= threshold)

    append_log(
        {
            "ts": now_utc(),
            "event": "predict",
            "proba_fraud": proba,
            "review": review,
            "threshold_cost": threshold,
            "n_features_received": len(tx.features),
        }
    )

    persist_single_prediction(
        input_features_json=tx.features,
        proba_fraud=proba,
        review=review,
        transaction_id=None,
    )

    return PredictionResponse(proba_fraud=proba, review=review, threshold_cost=threshold)


@app.post("/predict_batch", response_model=BatchResponse)
def predict_batch(req: BatchRequest):
    try:
        bundle = load_bundle()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    model = bundle["model"]
    feature_cols = bundle["feature_cols"]
    policy = load_policy()
    threshold = policy["threshold_cost"]
    max_alerts = policy["max_alerts"]

    n_total = len(req.transactions)
    if n_total == 0:
        persist_batch_predictions(
            transactions=[],
            results_valid=[],
            results_invalid=[],
            total_rows=0,
            valid_rows=0,
            invalid_rows=0,
            review_count=0,
            filename="api_batch",
        )
        return BatchResponse(
            threshold_cost=threshold,
            max_alerts=max_alerts,
            n_total=0,
            n_valid=0,
            n_invalid=0,
            n_candidates=0,
            n_review=0,
            results_valid=[],
            results_invalid=[],
        )

    valid_indices: list[int] = []
    invalid_items: list[BatchItemInvalid] = []
    invalid_items_persist: list[dict] = []

    for i, tx in enumerate(req.transactions):
        missing = [c for c in feature_cols if c not in tx.features]
        if missing:
            invalid_items.append(BatchItemInvalid(index=i, missing_features=missing))
            invalid_items_persist.append({"index": i, "missing_features": missing})
        else:
            valid_indices.append(i)

    n_valid = len(valid_indices)
    n_invalid = len(invalid_items)
    results_valid: list[BatchItemValid] = []
    results_valid_persist: list[dict] = []

    if n_valid > 0:
        x_values = np.zeros((n_valid, len(feature_cols)), dtype=float)
        for row_i, original_i in enumerate(valid_indices):
            feats = req.transactions[original_i].features
            x_values[row_i, :] = np.array([float(feats[c]) for c in feature_cols], dtype=float)

        probs = model.predict_proba(x_values)[:, 1].astype(float)
        candidates_mask = probs >= threshold
        candidate_indices = np.where(candidates_mask)[0]
        n_candidates = int(candidates_mask.sum())

        review_mask = np.zeros(n_valid, dtype=bool)
        rank = np.full(n_valid, -1, dtype=int)

        if n_candidates <= max_alerts:
            review_mask[candidate_indices] = True
            order = candidate_indices[np.argsort(-probs[candidate_indices])]
            for order_rank, idx in enumerate(order, start=1):
                rank[idx] = order_rank
        else:
            order = candidate_indices[np.argsort(-probs[candidate_indices])]
            selected = order[:max_alerts]
            review_mask[selected] = True
            for order_rank, idx in enumerate(selected, start=1):
                rank[idx] = order_rank

        for row_i, original_i in enumerate(valid_indices):
            item_proba = float(probs[row_i])
            item_review = int(review_mask[row_i])
            item_rank = int(rank[row_i]) if review_mask[row_i] else None
            results_valid.append(
                BatchItemValid(
                    index=original_i,
                    proba_fraud=item_proba,
                    review=item_review,
                    rank=item_rank,
                )
            )
            results_valid_persist.append(
                {
                    "index": original_i,
                    "proba_fraud": item_proba,
                    "review": item_review,
                    "rank": item_rank,
                }
            )

        n_review = int(review_mask.sum())

        append_log(
            {
                "ts": now_utc(),
                "event": "predict_batch",
                "threshold_cost": threshold,
                "max_alerts": max_alerts,
                "n_total": n_total,
                "n_valid": n_valid,
                "n_invalid": n_invalid,
                "n_candidates": n_candidates,
                "n_review": n_review,
                "proba_mean_valid": float(np.mean(probs)),
                "proba_p95_valid": float(np.quantile(probs, 0.95)),
            }
        )

        persist_batch_predictions(
            transactions=[tx.features for tx in req.transactions],
            results_valid=results_valid_persist,
            results_invalid=invalid_items_persist,
            total_rows=n_total,
            valid_rows=n_valid,
            invalid_rows=n_invalid,
            review_count=n_review,
            filename="api_batch",
        )

        return BatchResponse(
            threshold_cost=threshold,
            max_alerts=max_alerts,
            n_total=n_total,
            n_valid=n_valid,
            n_invalid=n_invalid,
            n_candidates=n_candidates,
            n_review=n_review,
            results_valid=results_valid,
            results_invalid=invalid_items,
        )

    append_log(
        {
            "ts": now_utc(),
            "event": "predict_batch",
            "threshold_cost": threshold,
            "max_alerts": max_alerts,
            "n_total": n_total,
            "n_valid": 0,
            "n_invalid": n_invalid,
            "n_candidates": 0,
            "n_review": 0,
            "note": "No valid transactions to score",
        }
    )

    persist_batch_predictions(
        transactions=[tx.features for tx in req.transactions],
        results_valid=[],
        results_invalid=invalid_items_persist,
        total_rows=n_total,
        valid_rows=0,
        invalid_rows=n_invalid,
        review_count=0,
        filename="api_batch",
    )

    return BatchResponse(
        threshold_cost=threshold,
        max_alerts=max_alerts,
        n_total=n_total,
        n_valid=0,
        n_invalid=n_invalid,
        n_candidates=0,
        n_review=0,
        results_valid=[],
        results_invalid=invalid_items,
    )


@app.post("/batch-jobs/upload", response_model=BatchUploadResponse)
async def upload_batch_job_csv(file: UploadFile = File(...)):
    filename = file.filename or "uploaded_batch.csv"
    is_csv_by_name = filename.lower().endswith(".csv")
    content_type = (file.content_type or "").lower()
    is_csv_by_content_type = content_type in CSV_ALLOWED_CONTENT_TYPES

    if not is_csv_by_name and not is_csv_by_content_type:
        raise HTTPException(status_code=400, detail="El archivo debe ser un CSV válido.")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="El CSV está vacío.")

    try:
        bundle = load_bundle()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    policy = load_policy()
    threshold = float(policy["threshold_cost"])
    max_alerts = int(policy["max_alerts"])

    try:
        scored_batch = parse_and_score_csv_batch(
            file_bytes=file_bytes,
            model=bundle["model"],
            feature_cols=bundle["feature_cols"],
            threshold=threshold,
            max_alerts=max_alerts,
            preview_limit=20,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected CSV parsing/scoring error: %s", exc)
        raise HTTPException(status_code=400, detail="No se pudo procesar el CSV.")

    try:
        batch_job_id = persist_uploaded_batch(filename=filename, scored_batch=scored_batch)
    except SQLAlchemyError as exc:
        logger.exception("Database error persisting uploaded batch: %s", exc)
        raise HTTPException(status_code=503, detail="Database unavailable.")
    except Exception as exc:
        logger.exception("Unexpected DB error persisting uploaded batch: %s", exc)
        raise HTTPException(status_code=503, detail="Database unavailable.")

    append_log(
        {
            "ts": now_utc(),
            "event": "batch_jobs_upload",
            "batch_job_id": batch_job_id,
            "filename": filename,
            "threshold_cost": threshold,
            "max_alerts": max_alerts,
            "total_rows": scored_batch["total_rows"],
            "valid_rows": scored_batch["valid_rows"],
            "invalid_rows": scored_batch["invalid_rows"],
            "review_count": scored_batch["review_count"],
        }
    )

    return BatchUploadResponse(
        batch_job_id=batch_job_id,
        filename=filename,
        status="completed",
        total_rows=scored_batch["total_rows"],
        valid_rows=scored_batch["valid_rows"],
        invalid_rows=scored_batch["invalid_rows"],
        review_count=scored_batch["review_count"],
        threshold_cost=threshold,
        max_alerts=max_alerts,
        results_preview=scored_batch["results_preview"],
    )


@app.get("/batch-jobs", response_model=list[BatchJobResponse])
def get_batch_jobs(
    limit: int = Query(20, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status: str | None = None,
    order: Literal["desc", "asc"] = "desc",
):
    return _run_db_read(
        "GET /batch-jobs",
        lambda db: [
            _serialize_batch_job(job)
            for job in list_batch_jobs(db, limit=limit, offset=offset, status=status, order=order)
        ],
    )


@app.get("/batch-jobs/{batch_job_id}", response_model=BatchJobResponse)
def get_batch_job(batch_job_id: int):
    def _query(db):
        job = get_batch_job_by_id(db, batch_job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Batch job not found.")
        return _serialize_batch_job(job)

    return _run_db_read("GET /batch-jobs/{batch_job_id}", _query)


@app.get("/batch-jobs/{batch_job_id}/predictions", response_model=list[PredictionSummaryResponse])
def get_batch_job_predictions(
    batch_job_id: int,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    only_invalid: bool = False,
    only_review: bool = False,
):
    def _query(db):
        job = get_batch_job_by_id(db, batch_job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Batch job not found.")
        rows = list_predictions_by_batch_job(
            db,
            batch_job_id=batch_job_id,
            limit=limit,
            offset=offset,
            only_invalid=only_invalid,
            only_review=only_review,
        )
        return [_serialize_prediction_summary(item) for item in rows]

    return _run_db_read("GET /batch-jobs/{batch_job_id}/predictions", _query)


@app.get("/batch-jobs/{batch_job_id}/download")
def download_batch_job_results(batch_job_id: int):
    def _query(db):
        job = get_batch_job_by_id(db, batch_job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Batch job not found.")

        rows = list_all_predictions_by_batch_job(db, batch_job_id=batch_job_id)

        fieldnames = [
            "prediction_id",
            "batch_job_id",
            "transaction_id",
            "proba_fraud",
            "review",
            "rank",
            "is_valid",
            "missing_features_json",
            "created_at",
        ]
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=fieldnames)
        writer.writeheader()

        for item in rows:
            writer.writerow(
                {
                    "prediction_id": item.id,
                    "batch_job_id": item.batch_job_id,
                    "transaction_id": item.transaction_id,
                    "proba_fraud": item.proba_fraud,
                    "review": bool(item.review),
                    "rank": item.rank,
                    "is_valid": bool(item.is_valid),
                    "missing_features_json": json.dumps(item.missing_features_json, ensure_ascii=False)
                    if item.missing_features_json is not None
                    else "",
                    "created_at": item.created_at.isoformat() if item.created_at else "",
                }
            )

        headers = {
            "Content-Disposition": f'attachment; filename="batch_job_{batch_job_id}_results.csv"'
        }
        return Response(content=buffer.getvalue(), media_type="text/csv; charset=utf-8", headers=headers)

    return _run_db_read("GET /batch-jobs/{batch_job_id}/download", _query)


@app.get("/predictions", response_model=list[PredictionSummaryResponse])
def get_predictions(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    only_invalid: bool = False,
    only_review: bool = False,
    batch_job_id: int | None = None,
):
    return _run_db_read(
        "GET /predictions",
        lambda db: [
            _serialize_prediction_summary(item)
            for item in list_predictions(
                db,
                limit=limit,
                offset=offset,
                only_invalid=only_invalid,
                only_review=only_review,
                batch_job_id=batch_job_id,
            )
        ],
    )


@app.get("/predictions/{prediction_id}", response_model=PredictionDetailResponse)
def get_prediction(prediction_id: int):
    def _query(db):
        item = get_prediction_by_id(db, prediction_id)
        if item is None:
            raise HTTPException(status_code=404, detail="Prediction not found.")
        return _serialize_prediction_detail(item)

    return _run_db_read("GET /predictions/{prediction_id}", _query)


@app.get("/audit-events", response_model=list[AuditEventResponse])
def get_audit_events(
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    event_type: str | None = None,
    entity_type: str | None = None,
):
    return _run_db_read(
        "GET /audit-events",
        lambda db: [
            _serialize_audit_event(item)
            for item in list_audit_events(
                db,
                limit=limit,
                offset=offset,
                event_type=event_type,
                entity_type=entity_type,
            )
        ],
    )


@app.get("/model-versions", response_model=list[ModelVersionResponse])
def get_model_versions(
    limit: int = Query(20, ge=1, le=500),
    offset: int = Query(0, ge=0),
    only_active: bool = False,
):
    return _run_db_read(
        "GET /model-versions",
        lambda db: [
            _serialize_model_version(item)
            for item in list_model_versions(db, limit=limit, offset=offset, only_active=only_active)
        ],
    )


@app.get("/model-versions/active", response_model=ModelVersionResponse)
def get_active_model_version_endpoint():
    def _query(db):
        item = get_active_model_version(db)
        if item is None:
            raise HTTPException(status_code=404, detail="No active model version found.")
        return _serialize_model_version(item)

    return _run_db_read("GET /model-versions/active", _query)


@app.post("/reports", response_model=ReportResponse)
def create_report(payload: ReportCreateRequest):
    try:
        with SessionLocal() as db:
            report = create_report_from_request(db, payload)
            db.commit()
            db.refresh(report)
            return _serialize_report(report)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except SQLAlchemyError as exc:
        logger.exception("Database error creating report: %s", exc)
        raise HTTPException(status_code=503, detail="Database unavailable.")
    except Exception as exc:
        logger.exception("Unexpected error creating report: %s", exc)
        raise HTTPException(status_code=500, detail="Could not create report.")


@app.get("/reports", response_model=list[ReportResponse])
def get_reports(
    limit: int = Query(20, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    return _run_db_read(
        "GET /reports",
        lambda db: [_serialize_report(item) for item in list_reports(db, limit=limit, offset=offset)],
    )


@app.get("/reports/{report_id}", response_model=ReportResponse)
def get_report(report_id: int):
    def _query(db):
        report = get_report_by_id(db, report_id)
        if report is None:
            raise HTTPException(status_code=404, detail="Report not found.")
        return _serialize_report(report)

    return _run_db_read("GET /reports/{report_id}", _query)


@app.get("/reports/{report_id}/download")
def download_report(report_id: int):
    def _query(db):
        report = get_report_by_id(db, report_id)
        if report is None:
            raise HTTPException(status_code=404, detail="Report not found.")
        return {
            "id": report.id,
            "report_code": report.report_code,
            "format": report.format,
            "file_path": report.file_path,
        }

    report_data = _run_db_read("GET /reports/{report_id}/download", _query)
    report_path = _resolve_report_download_path(report_data.get("file_path"))

    write_audit_event_best_effort(
        event_type="REPORT_DOWNLOADED",
        entity_type="report",
        entity_id=str(report_data["id"]),
        details_json={
            "report_code": report_data["report_code"],
            "format": report_data["format"],
        },
        user_id=None,
    )

    report_format = str(report_data.get("format", "")).lower()
    if report_format == "json":
        media_type = "application/json"
        extension = "json"
    elif report_format == "csv":
        media_type = "text/csv; charset=utf-8"
        extension = "csv"
    else:
        media_type = "application/octet-stream"
        extension = "bin"

    return FileResponse(
        path=report_path,
        media_type=media_type,
        filename=f"{report_data['report_code']}.{extension}",
    )


@app.get("/drift-runs", response_model=list[DriftRunResponse])
def get_drift_runs(
    limit: int = Query(20, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    return _run_db_read(
        "GET /drift-runs",
        lambda db: [_serialize_drift_run(item) for item in list_drift_runs(db, limit=limit, offset=offset)],
    )


