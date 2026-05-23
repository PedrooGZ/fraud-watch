from datetime import datetime

from pydantic import BaseModel


class DashboardActivePolicy(BaseModel):
    threshold_cost: float
    max_alerts: int
    priority_mode: str
    error_cost_mode: str


class DashboardActiveModel(BaseModel):
    id: int
    name: str
    model_type: str
    pr_auc: float
    brier_score: float
    n_features: int
    created_at: datetime


class DashboardSummaryResponse(BaseModel):
    total_predictions: int
    valid_predictions: int
    invalid_predictions: int
    review_count: int
    recent_predictions: int
    batch_jobs_count: int
    completed_batch_jobs: int
    failed_batch_jobs: int
    latest_batch_created_at: datetime | None
    latest_prediction_created_at: datetime | None
    active_policy: DashboardActivePolicy | None
    active_model: DashboardActiveModel | None


class DashboardPriorityCaseResponse(BaseModel):
    id: int
    batch_job_id: int | None
    model_version_id: int | None
    transaction_id: str | None
    proba_fraud: float | None
    review: bool
    rank: int | None
    is_valid: bool
    created_at: datetime
