from __future__ import annotations

import logging

import numpy as np
from sqlalchemy.orm import Session

from src.core.config import ARTIFACTS_DIR
from src.db.models import DriftRun
from src.repositories.drift_repository import create_drift_run

logger = logging.getLogger(__name__)


def calculate_psi(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    expected_arr = np.asarray(expected, dtype=float).ravel()
    actual_arr = np.asarray(actual, dtype=float).ravel()

    if expected_arr.size == 0 or actual_arr.size == 0:
        raise ValueError("Expected and actual arrays must contain values.")

    cuts = np.quantile(expected_arr, np.linspace(0, 1, bins + 1))
    cuts[0] = -np.inf
    cuts[-1] = np.inf

    exp_counts, _ = np.histogram(expected_arr, bins=cuts)
    act_counts, _ = np.histogram(actual_arr, bins=cuts)

    exp_dist = exp_counts / max(exp_counts.sum(), 1)
    act_dist = act_counts / max(act_counts.sum(), 1)

    eps = 1e-6
    exp_dist = np.clip(exp_dist, eps, None)
    act_dist = np.clip(act_dist, eps, None)

    return float(np.sum((act_dist - exp_dist) * np.log(act_dist / exp_dist)))


def classify_psi(psi: float) -> str:
    if psi < 0.1:
        return "stable"
    if psi <= 0.25:
        return "warning"
    return "drift"


def try_create_drift_run_for_scores(
    db: Session,
    *,
    new_scores: list[float] | np.ndarray,
    batch_job_id: int | None = None,
    bins: int = 10,
) -> DriftRun | None:
    try:
        new_scores_arr = np.asarray(new_scores, dtype=float).ravel()
        if new_scores_arr.size == 0:
            logger.warning("No valid scores available; skipping drift run creation")
            return None

        ref_scores_path = ARTIFACTS_DIR / "ref_scores.npy"
        if not ref_scores_path.exists():
            logger.warning("ref_scores.npy not found; skipping drift run creation")
            return None

        try:
            ref_scores_arr = np.asarray(np.load(ref_scores_path), dtype=float).ravel()
        except Exception:
            logger.exception("Could not load ref_scores.npy; skipping drift run creation")
            return None

        if ref_scores_arr.size == 0:
            logger.warning("ref_scores.npy is empty; skipping drift run creation")
            return None

        psi = calculate_psi(ref_scores_arr, new_scores_arr, bins=bins)
        drift_run = create_drift_run(
            db,
            psi=psi,
            status=classify_psi(psi),
            bins=bins,
            sample_size=int(new_scores_arr.size),
            amount_multiplier=1.0,
            ref_mean=float(np.mean(ref_scores_arr)),
            ref_p95=float(np.quantile(ref_scores_arr, 0.95)),
            new_mean=float(np.mean(new_scores_arr)),
            new_p95=float(np.quantile(new_scores_arr, 0.95)),
            summary_path=f"batch_upload:{batch_job_id}" if batch_job_id is not None else None,
        )
        logger.info("Created drift_run for batch_job_id=%s", batch_job_id)
        return drift_run
    except Exception:
        logger.exception("Failed to create drift run; continuing without drift persistence")
        return None
