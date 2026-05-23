from fastapi.testclient import TestClient
import pytest
import csv
import io
from pathlib import Path
import uuid

import src.api.app as app_module
from src.api.app import app
from src.core.config import ARTIFACTS_DIR
from src.services.drift_service import classify_psi

client = TestClient(app)


def test_healthcheck():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "policy" in body


def test_policy_endpoint():
    response = client.get("/policy")
    assert response.status_code == 200
    body = response.json()
    assert "policy" in body
    assert "threshold_cost" in body["policy"]
    assert "max_alerts" in body["policy"]


def _build_unique_email() -> str:
    return f"test_{uuid.uuid4().hex}@example.com"


def _register_auth_user_or_skip(
    *,
    role: str = "analyst",
    password: str = "password123",
):
    _require_db_or_skip()
    payload = {
        "email": _build_unique_email(),
        "full_name": "Auth Test User",
        "password": password,
        "role": role,
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code in (200, 201)
    return payload, response


def _auth_headers_for_role_or_skip(role: str) -> dict[str, str]:
    _, register_response = _register_auth_user_or_skip(role=role, password="policypass123")
    token = register_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_register_user():
    payload, response = _register_auth_user_or_skip()
    body = response.json()
    assert body.get("access_token")
    assert body.get("token_type") == "bearer"
    assert body.get("user", {}).get("email") == payload["email"].lower()
    assert body.get("user", {}).get("full_name") == payload["full_name"]
    assert body.get("user", {}).get("role") == payload["role"]


def test_register_duplicate_email_rejected():
    _require_db_or_skip()
    email = _build_unique_email()
    payload = {
        "email": email,
        "full_name": "Duplicate User",
        "password": "password123",
        "role": "analyst",
    }
    first = client.post("/auth/register", json=payload)
    assert first.status_code in (200, 201)
    second = client.post("/auth/register", json=payload)
    assert second.status_code == 400


def test_login_user():
    payload, _ = _register_auth_user_or_skip(password="authpass123")
    login_response = client.post(
        "/auth/login",
        json={"email": payload["email"], "password": "authpass123"},
    )
    assert login_response.status_code == 200
    body = login_response.json()
    assert body.get("access_token")
    assert body.get("token_type") == "bearer"
    assert body.get("user", {}).get("email") == payload["email"].lower()


def test_login_invalid_password():
    payload, _ = _register_auth_user_or_skip(password="validpass123")
    login_response = client.post(
        "/auth/login",
        json={"email": payload["email"], "password": "wrongpass123"},
    )
    assert login_response.status_code == 401


def test_auth_me():
    _, register_response = _register_auth_user_or_skip(password="mepass123")
    token = register_response.json()["access_token"]

    me_response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    body = me_response.json()
    assert body.get("id") is not None
    assert body.get("email")
    assert body.get("full_name")


def test_auth_me_without_token():
    _require_db_or_skip()
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_auth_me_invalid_token():
    _require_db_or_skip()
    response = client.get("/auth/me", headers={"Authorization": "Bearer invalid.token.value"})
    assert response.status_code == 401


def test_put_policy_requires_auth():
    _require_db_or_skip()
    put_payload = {
        "threshold_cost": 0.23,
        "max_alerts": 230,
        "priority_mode": "risk",
        "error_cost_mode": "balanced",
        "reason": "auth required check",
    }
    response = client.put("/policy", json=put_payload)
    assert response.status_code == 401


def test_put_policy_rejects_analyst():
    _require_db_or_skip()
    analyst_headers = _auth_headers_for_role_or_skip("analyst")
    put_payload = {
        "threshold_cost": 0.26,
        "max_alerts": 260,
        "priority_mode": "impact",
        "error_cost_mode": "reduce_fp",
        "reason": "analyst forbidden check",
    }
    response = client.put("/policy", json=put_payload, headers=analyst_headers)
    assert response.status_code == 403


def test_put_policy_allows_admin():
    _require_db_or_skip()
    admin_headers = _auth_headers_for_role_or_skip("admin")
    get_response = client.get("/policy")
    assert get_response.status_code == 200
    current = get_response.json()["policy"]

    new_threshold = 0.33 if float(current["threshold_cost"]) != 0.33 else 0.34
    new_max_alerts = 333 if int(current["max_alerts"]) != 333 else 334
    put_payload = {
        "threshold_cost": new_threshold,
        "max_alerts": new_max_alerts,
        "priority_mode": "mixed",
        "error_cost_mode": "reduce_fn",
        "reason": "admin allowed check",
    }
    put_response = client.put("/policy", json=put_payload, headers=admin_headers)
    assert put_response.status_code == 200

    policy_after = client.get("/policy")
    assert policy_after.status_code == 200
    body = policy_after.json()["policy"]
    assert float(body["threshold_cost"]) == new_threshold
    assert int(body["max_alerts"]) == new_max_alerts


def _build_valid_features_or_skip() -> dict[str, float]:
    try:
        bundle = app_module.load_bundle()
    except Exception as exc:
        pytest.skip(f"Modelo no disponible para test de prediccion: {exc}")
    feature_cols = bundle["feature_cols"]
    return {col: 0.0 for col in feature_cols}


def _require_db_or_skip():
    sqlalchemy = pytest.importorskip("sqlalchemy")
    from src.db.session import engine

    try:
        with engine.connect() as connection:
            connection.execute(sqlalchemy.text("SELECT 1"))
    except Exception:
        pytest.skip("PostgreSQL no disponible para este test.")

    from scripts.init_db import main as init_db_main

    init_db_main()


def _ensure_batch_and_predictions_data():
    features = _build_valid_features_or_skip()
    client.post("/predict", json={"features": features})
    client.post(
        "/predict_batch",
        json={
            "transactions": [
                {"features": features},
                {"features": {}},
            ]
        },
    )


def test_policy_endpoint_db_source_if_db_available():
    _require_db_or_skip()
    response = client.get("/policy")
    assert response.status_code == 200
    body = response.json()
    assert body["policy"]["source"] == "database"
    assert "threshold_cost" in body["policy"]
    assert "max_alerts" in body["policy"]


def test_predict_endpoint():
    features = _build_valid_features_or_skip()
    response = client.post("/predict", json={"features": features})
    assert response.status_code == 200
    body = response.json()
    assert "proba_fraud" in body
    assert "review" in body
    assert "threshold_cost" in body


def test_predict_batch_endpoint():
    features = _build_valid_features_or_skip()
    payload = {
        "transactions": [
            {"features": features},
            {"features": {}},
        ]
    }
    response = client.post("/predict_batch", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["n_total"] == 2
    assert "results_valid" in body
    assert "results_invalid" in body


def test_get_batch_jobs_with_db():
    _require_db_or_skip()
    _ensure_batch_and_predictions_data()
    response = client.get("/batch-jobs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_predictions_with_db():
    _require_db_or_skip()
    _ensure_batch_and_predictions_data()
    response = client.get("/predictions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_batch_job_predictions_with_db():
    _require_db_or_skip()
    _ensure_batch_and_predictions_data()
    jobs_response = client.get("/batch-jobs")
    assert jobs_response.status_code == 200
    jobs = jobs_response.json()
    assert len(jobs) > 0
    batch_id = jobs[0]["id"]

    response = client.get(f"/batch-jobs/{batch_id}/predictions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_policy_history_endpoint():
    _require_db_or_skip()
    response = client.get("/policy/history")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_put_policy_updates_and_get_policy_reflects_change():
    _require_db_or_skip()
    admin_headers = _auth_headers_for_role_or_skip("admin")
    get_response = client.get("/policy")
    assert get_response.status_code == 200
    current = get_response.json()["policy"]

    new_threshold = 0.31 if float(current["threshold_cost"]) != 0.31 else 0.29
    new_max_alerts = 321 if int(current["max_alerts"]) != 321 else 322

    put_payload = {
        "threshold_cost": new_threshold,
        "max_alerts": new_max_alerts,
        "priority_mode": "risk",
        "error_cost_mode": "balanced",
        "reason": "test update",
    }
    put_response = client.put("/policy", json=put_payload, headers=admin_headers)
    assert put_response.status_code == 200

    policy_after = client.get("/policy")
    assert policy_after.status_code == 200
    body = policy_after.json()["policy"]
    assert float(body["threshold_cost"]) == new_threshold
    assert int(body["max_alerts"]) == new_max_alerts


def test_put_policy_creates_policy_history():
    _require_db_or_skip()
    admin_headers = _auth_headers_for_role_or_skip("admin")
    put_payload = {
        "threshold_cost": 0.27,
        "max_alerts": 280,
        "priority_mode": "mixed",
        "error_cost_mode": "reduce_fn",
        "reason": "history check",
    }
    put_response = client.put("/policy", json=put_payload, headers=admin_headers)
    assert put_response.status_code == 200

    history_response = client.get("/policy/history")
    assert history_response.status_code == 200
    history = history_response.json()
    assert len(history) > 0
    assert "new_values_json" in history[0]


def test_put_policy_creates_audit_event():
    _require_db_or_skip()
    admin_headers = _auth_headers_for_role_or_skip("admin")
    put_payload = {
        "threshold_cost": 0.24,
        "max_alerts": 240,
        "priority_mode": "impact",
        "error_cost_mode": "reduce_fp",
        "reason": "audit check",
    }
    put_response = client.put("/policy", json=put_payload, headers=admin_headers)
    assert put_response.status_code == 200

    audit_response = client.get("/audit-events?event_type=POLICY_UPDATED")
    assert audit_response.status_code == 200
    events = audit_response.json()
    assert len(events) > 0
    assert events[0]["event_type"] == "POLICY_UPDATED"


def test_get_audit_events():
    _require_db_or_skip()
    response = client.get("/audit-events")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_model_versions_active():
    _require_db_or_skip()
    response = client.get("/model-versions/active")
    assert response.status_code == 200
    body = response.json()
    assert body["is_active"] is True


def test_get_dashboard_summary_with_db():
    _require_db_or_skip()
    _ensure_batch_and_predictions_data()
    response = client.get("/dashboard/summary")
    assert response.status_code == 200
    body = response.json()
    assert "total_predictions" in body
    assert "valid_predictions" in body
    assert "invalid_predictions" in body
    assert "review_count" in body
    assert "batch_jobs_count" in body
    assert "active_policy" in body
    assert "active_model" in body


def test_get_dashboard_priority_cases():
    _require_db_or_skip()
    _ensure_batch_and_predictions_data()
    response = client.get("/dashboard/priority-cases")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_dashboard_priority_cases_only_review():
    _require_db_or_skip()
    _ensure_batch_and_predictions_data()
    response = client.get("/dashboard/priority-cases?only_review=true&limit=10")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_reports():
    _require_db_or_skip()
    response = client.get("/reports")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_report_json_with_db():
    _require_db_or_skip()
    payload = {
        "period": "last_30_days",
        "format": "json",
        "detail_level": "executive",
        "sections": ["summary", "analytics", "drift", "model"],
    }
    response = client.post("/reports", json=payload)
    assert response.status_code in (200, 201)
    body = response.json()
    assert body.get("report_code")
    assert body.get("format") == "json"
    assert body.get("file_path")
    assert "sections_json" in body
    file_path = Path(body["file_path"])
    assert file_path.exists()


def test_create_report_csv_with_db():
    _require_db_or_skip()
    payload = {
        "period": "last_30_days",
        "format": "csv",
        "detail_level": "executive",
        "sections": ["summary", "analytics", "drift", "model"],
    }
    response = client.post("/reports", json=payload)
    assert response.status_code in (200, 201)
    body = response.json()
    assert body.get("report_code")
    assert body.get("format") == "csv"
    assert body.get("file_path")
    assert str(body["file_path"]).lower().endswith(".csv")


def test_get_reports_includes_created_report():
    _require_db_or_skip()
    payload = {
        "period": "last_7_days",
        "format": "json",
        "detail_level": "operational",
        "sections": ["summary", "batch_jobs"],
    }
    create_response = client.post("/reports", json=payload)
    assert create_response.status_code in (200, 201)
    report_code = create_response.json()["report_code"]

    list_response = client.get("/reports")
    assert list_response.status_code == 200
    reports = list_response.json()
    assert any(item.get("report_code") == report_code for item in reports)


def test_create_report_rejects_unsupported_format():
    _require_db_or_skip()
    payload = {
        "period": "last_30_days",
        "format": "pdf",
        "detail_level": "executive",
        "sections": ["summary"],
    }
    response = client.post("/reports", json=payload)
    assert response.status_code in (400, 422)


def test_create_report_rejects_empty_sections():
    _require_db_or_skip()
    payload = {
        "period": "last_30_days",
        "format": "json",
        "detail_level": "executive",
        "sections": [],
    }
    response = client.post("/reports", json=payload)
    assert response.status_code in (400, 422)


def test_get_report_by_id():
    _require_db_or_skip()
    create_payload = {
        "period": "last_30_days",
        "format": "json",
        "detail_level": "executive",
        "sections": ["summary", "analytics"],
    }
    create_response = client.post("/reports", json=create_payload)
    assert create_response.status_code in (200, 201)
    created = create_response.json()

    response = client.get(f"/reports/{created['id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created["id"]
    assert body.get("report_code")
    assert body.get("format") == "json"


def test_get_report_by_id_not_found():
    _require_db_or_skip()
    response = client.get("/reports/999999999")
    assert response.status_code == 404


def test_download_report_json():
    _require_db_or_skip()
    create_payload = {
        "period": "last_30_days",
        "format": "json",
        "detail_level": "executive",
        "sections": ["summary", "model"],
    }
    create_response = client.post("/reports", json=create_payload)
    assert create_response.status_code in (200, 201)
    created = create_response.json()

    response = client.get(f"/reports/{created['id']}/download")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert "attachment;" in response.headers.get("content-disposition", "")
    assert created["report_code"] in response.text


def test_download_report_csv():
    _require_db_or_skip()
    create_payload = {
        "period": "last_30_days",
        "format": "csv",
        "detail_level": "executive",
        "sections": ["summary", "analytics", "drift", "model"],
    }
    create_response = client.post("/reports", json=create_payload)
    assert create_response.status_code in (200, 201)
    created = create_response.json()

    response = client.get(f"/reports/{created['id']}/download")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment;" in response.headers.get("content-disposition", "")
    csv_text = response.text
    assert "section,key,value" in csv_text
    assert created["report_code"] in csv_text


def test_download_report_not_found():
    _require_db_or_skip()
    response = client.get("/reports/999999999/download")
    assert response.status_code == 404


def test_get_drift_runs():
    _require_db_or_skip()
    response = client.get("/drift-runs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_analytics_fraud_evolution():
    _require_db_or_skip()
    _ensure_batch_and_predictions_data()
    response = client.get("/analytics/fraud-evolution?days=30")
    assert response.status_code == 200
    body = response.json()
    assert "period_days" in body
    assert "points" in body
    assert isinstance(body["points"], list)


def test_get_analytics_risk_distribution():
    _require_db_or_skip()
    _ensure_batch_and_predictions_data()
    response = client.get("/analytics/risk-distribution")
    assert response.status_code == 200
    body = response.json()
    assert "low" in body
    assert "medium" in body
    assert "high" in body
    assert "total" in body
    assert "thresholds" in body


def test_get_analytics_classification_summary():
    _require_db_or_skip()
    _ensure_batch_and_predictions_data()
    response = client.get("/analytics/classification-summary")
    assert response.status_code == 200
    body = response.json()
    assert "review" in body
    assert "no_review" in body
    assert "invalid" in body
    assert "total" in body


def test_get_analytics_variable_importance():
    _require_db_or_skip()
    response = client.get("/analytics/variable-importance")
    assert response.status_code == 200
    body = response.json()
    assert "source" in body
    assert "items" in body
    assert isinstance(body["items"], list)


def test_get_analytics_variable_importance_limit():
    _require_db_or_skip()
    response = client.get("/analytics/variable-importance?limit=5")
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) <= 5


def _build_upload_csv_bytes_or_skip(with_invalid_row: bool = False) -> bytes:
    features = _build_valid_features_or_skip()
    fieldnames = list(features.keys())
    if not fieldnames:
        pytest.skip("No hay columnas de features disponibles para test de CSV.")

    valid_row = {column: "0.0" for column in fieldnames}
    rows = [valid_row]
    if with_invalid_row:
        invalid_row = {column: "0.0" for column in fieldnames}
        invalid_row[fieldnames[0]] = ""
        rows.append(invalid_row)

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buffer.getvalue().encode("utf-8")


def test_upload_batch_job_csv_valid():
    _require_db_or_skip()
    csv_bytes = _build_upload_csv_bytes_or_skip(with_invalid_row=False)

    response = client.post(
        "/batch-jobs/upload",
        files={"file": ("valid.csv", csv_bytes, "text/csv")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["total_rows"] >= 1
    assert body["valid_rows"] >= 1
    assert "batch_job_id" in body


def test_upload_batch_job_csv_with_invalid_row():
    _require_db_or_skip()
    csv_bytes = _build_upload_csv_bytes_or_skip(with_invalid_row=True)

    response = client.post(
        "/batch-jobs/upload",
        files={"file": ("mixed.csv", csv_bytes, "text/csv")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["invalid_rows"] > 0
    assert body["total_rows"] >= 2
    assert any(item["is_valid"] is False for item in body["results_preview"])


def test_upload_batch_job_csv_rejects_non_csv():
    _require_db_or_skip()
    response = client.post(
        "/batch-jobs/upload",
        files={"file": ("not_csv.txt", b"plain text", "text/plain")},
    )
    assert response.status_code == 400


def test_download_batch_job_results_csv():
    _require_db_or_skip()
    csv_bytes = _build_upload_csv_bytes_or_skip(with_invalid_row=True)
    upload_response = client.post(
        "/batch-jobs/upload",
        files={"file": ("for_download.csv", csv_bytes, "text/csv")},
    )
    assert upload_response.status_code == 200
    batch_job_id = upload_response.json()["batch_job_id"]

    response = client.get(f"/batch-jobs/{batch_job_id}/download")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment;" in response.headers.get("content-disposition", "")
    csv_text = response.text
    assert "prediction_id" in csv_text
    assert "batch_job_id" in csv_text


def test_upload_batch_job_csv_creates_drift_run_when_ref_scores_available():
    _require_db_or_skip()
    ref_scores_path = ARTIFACTS_DIR / "ref_scores.npy"
    if not ref_scores_path.exists():
        pytest.skip("ref_scores.npy no existe; no se valida creación automática de drift.")

    csv_bytes = _build_upload_csv_bytes_or_skip(with_invalid_row=False)
    upload_response = client.post(
        "/batch-jobs/upload",
        files={"file": ("drift_check.csv", csv_bytes, "text/csv")},
    )
    assert upload_response.status_code == 200
    batch_job_id = upload_response.json()["batch_job_id"]

    drift_response = client.get("/drift-runs?limit=100")
    assert drift_response.status_code == 200
    drift_runs = drift_response.json()
    assert isinstance(drift_runs, list)
    assert len(drift_runs) > 0

    batch_marker = f"batch_upload:{batch_job_id}"
    batch_drift = next((item for item in drift_runs if item.get("summary_path") == batch_marker), None)
    assert batch_drift is not None
    assert "psi" in batch_drift
    assert "status" in batch_drift
    assert "sample_size" in batch_drift
    assert "ref_mean" in batch_drift
    assert "new_mean" in batch_drift


def test_classify_psi_ranges():
    assert classify_psi(0.05) == "stable"
    assert classify_psi(0.1) == "warning"
    assert classify_psi(0.25) == "warning"
    assert classify_psi(0.3) == "drift"
