import {
  formatBooleanReview,
  formatDate,
  formatDateShort,
  formatProbability,
  formatReportDetailLevel,
  formatReportFormat,
  formatReportPeriod,
  formatValidity,
  toBooleanFlag,
} from "./formatters";

const PRIORITY_MODES = ["risk", "impact", "mixed"];
const ERROR_COST_MODES = ["balanced", "reduce_fp", "reduce_fn"];

export function normalizePolicy(apiPolicy) {
  const payload = apiPolicy?.policy ? apiPolicy.policy : apiPolicy || {};
  return {
    threshold_cost: Number(payload.threshold_cost ?? 0.02),
    max_alerts: Number(payload.max_alerts ?? 500),
    priority_mode: PRIORITY_MODES.includes(payload.priority_mode) ? payload.priority_mode : "risk",
    error_cost_mode: ERROR_COST_MODES.includes(payload.error_cost_mode) ? payload.error_cost_mode : "balanced",
    source: payload.source || "json_fallback",
  };
}

export function policyUiToPayload(uiState) {
  const threshold = Number(uiState.threshold_cost);
  const maxAlerts = Number(uiState.max_alerts);

  return {
    threshold_cost: Number.isNaN(threshold) ? 0.02 : Math.min(1, Math.max(0, threshold)),
    max_alerts: Number.isNaN(maxAlerts) ? 0 : Math.max(0, Math.trunc(maxAlerts)),
    priority_mode: PRIORITY_MODES.includes(uiState.priority_mode) ? uiState.priority_mode : "risk",
    error_cost_mode: ERROR_COST_MODES.includes(uiState.error_cost_mode) ? uiState.error_cost_mode : "balanced",
  };
}

export function normalizePrediction(apiPrediction) {
  const prediction = apiPrediction || {};
  const review = toBooleanFlag(prediction.review);
  const isValid = toBooleanFlag(prediction.is_valid);
  return {
    id: prediction.id,
    batch_job_id: prediction.batch_job_id ?? null,
    model_version_id: prediction.model_version_id ?? null,
    transaction_id: prediction.transaction_id ?? null,
    proba_fraud: prediction.proba_fraud ?? null,
    proba_fraud_label: formatProbability(prediction.proba_fraud),
    review,
    review_label: formatBooleanReview(prediction.review),
    rank: prediction.rank ?? null,
    is_valid: isValid,
    is_valid_label: formatValidity(prediction.is_valid),
    missing_features_json: prediction.missing_features_json ?? null,
    created_at: prediction.created_at ?? null,
    created_at_label: formatDate(prediction.created_at),
  };
}

export function normalizeBatchJob(apiBatchJob) {
  const batchJob = apiBatchJob || {};
  return {
    id: batchJob.id,
    filename: batchJob.filename || "api_batch",
    status: batchJob.status || "unknown",
    total_rows: Number(batchJob.total_rows ?? 0),
    valid_rows: Number(batchJob.valid_rows ?? 0),
    invalid_rows: Number(batchJob.invalid_rows ?? 0),
    review_count: Number(batchJob.review_count ?? 0),
    error_message: batchJob.error_message || null,
    created_at: batchJob.created_at || null,
    created_at_label: formatDate(batchJob.created_at),
    finished_at: batchJob.finished_at || null,
    finished_at_label: formatDate(batchJob.finished_at),
  };
}

export function normalizeReport(apiReport) {
  const report = apiReport || {};
  return {
    id: report.id,
    report_code: report.report_code || "N/A",
    period: report.period || "N/A",
    period_label: formatReportPeriod(report.period),
    format: report.format || "N/A",
    format_label: formatReportFormat(report.format),
    detail_level: report.detail_level || "N/A",
    detail_level_label: formatReportDetailLevel(report.detail_level),
    sections_json: report.sections_json || [],
    file_path: report.file_path || null,
    generated_by_user_id: report.generated_by_user_id ?? null,
    created_at: report.created_at || null,
    created_at_label: formatDate(report.created_at),
  };
}

export function normalizeDriftRun(apiDriftRun) {
  const driftRun = apiDriftRun || {};
  return {
    id: driftRun.id,
    psi: driftRun.psi ?? null,
    status: driftRun.status || "N/A",
    bins: driftRun.bins ?? null,
    sample_size: driftRun.sample_size ?? null,
    amount_multiplier: driftRun.amount_multiplier ?? null,
    created_at: driftRun.created_at || null,
    created_at_label: formatDate(driftRun.created_at),
  };
}

export function normalizeDashboardSummary(apiSummary) {
  const summary = apiSummary || {};
  const activePolicyRaw = summary.active_policy || null;
  const activeModelRaw = summary.active_model || null;

  return {
    total_predictions: Number(summary.total_predictions ?? 0),
    valid_predictions: Number(summary.valid_predictions ?? 0),
    invalid_predictions: Number(summary.invalid_predictions ?? 0),
    review_count: Number(summary.review_count ?? 0),
    recent_predictions: Number(summary.recent_predictions ?? summary.total_predictions ?? 0),
    batch_jobs_count: Number(summary.batch_jobs_count ?? 0),
    completed_batch_jobs: Number(summary.completed_batch_jobs ?? 0),
    failed_batch_jobs: Number(summary.failed_batch_jobs ?? 0),
    latest_batch_created_at: summary.latest_batch_created_at ?? null,
    latest_batch_created_at_label: formatDate(summary.latest_batch_created_at),
    latest_prediction_created_at: summary.latest_prediction_created_at ?? null,
    latest_prediction_created_at_label: formatDate(summary.latest_prediction_created_at),
    active_policy: activePolicyRaw
      ? {
        threshold_cost: Number(activePolicyRaw.threshold_cost ?? 0.02),
        max_alerts: Number(activePolicyRaw.max_alerts ?? 500),
        priority_mode: activePolicyRaw.priority_mode || "risk",
        error_cost_mode: activePolicyRaw.error_cost_mode || "balanced",
      }
      : null,
    active_model: activeModelRaw
      ? {
        id: activeModelRaw.id ?? null,
        name: activeModelRaw.name || "N/A",
        model_type: activeModelRaw.model_type || "N/A",
        pr_auc: activeModelRaw.pr_auc ?? null,
        brier_score: activeModelRaw.brier_score ?? null,
        n_features: activeModelRaw.n_features ?? null,
        created_at: activeModelRaw.created_at ?? null,
        created_at_label: formatDate(activeModelRaw.created_at),
      }
      : null,
  };
}

export function normalizeDashboardPriorityCase(apiCase) {
  const row = apiCase || {};
  const review = toBooleanFlag(row.review);
  const isValid = toBooleanFlag(row.is_valid);
  return {
    id: row.id ?? null,
    batch_job_id: row.batch_job_id ?? null,
    model_version_id: row.model_version_id ?? null,
    transaction_id: row.transaction_id ?? null,
    proba_fraud: row.proba_fraud ?? null,
    proba_fraud_label: formatProbability(row.proba_fraud),
    review,
    review_label: formatBooleanReview(row.review),
    rank: row.rank ?? null,
    is_valid: isValid,
    is_valid_label: formatValidity(row.is_valid),
    created_at: row.created_at ?? null,
    created_at_label: formatDate(row.created_at),
  };
}

export function normalizeFraudEvolution(apiResponse) {
  const payload = apiResponse || {};
  const points = Array.isArray(payload.points) ? payload.points : [];

  return points.map((point) => {
    const total = Number(point?.total_predictions ?? 0);
    const review = Number(point?.review_count ?? 0);
    const invalid = Number(point?.invalid_count ?? 0);
    return {
      label: formatDateShort(point?.date),
      total: Number.isNaN(total) ? 0 : total,
      review: Number.isNaN(review) ? 0 : review,
      invalid: Number.isNaN(invalid) ? 0 : invalid,
      date: point?.date ?? null,
    };
  });
}

export function normalizeRiskDistribution(apiResponse) {
  const payload = apiResponse || {};
  const low = Number(payload.low ?? 0);
  const medium = Number(payload.medium ?? 0);
  const high = Number(payload.high ?? 0);

  return [
    { label: "Bajo", value: Number.isNaN(low) ? 0 : low },
    { label: "Medio", value: Number.isNaN(medium) ? 0 : medium },
    { label: "Alto", value: Number.isNaN(high) ? 0 : high },
  ];
}

export function normalizeClassificationSummary(apiResponse) {
  const payload = apiResponse || {};
  const review = Number(payload.review ?? 0);
  const noReview = Number(payload.no_review ?? 0);
  const invalid = Number(payload.invalid ?? 0);

  return [
    { label: "Revisión", value: Number.isNaN(review) ? 0 : review },
    { label: "No revisión", value: Number.isNaN(noReview) ? 0 : noReview },
    { label: "Inválidas", value: Number.isNaN(invalid) ? 0 : invalid },
  ];
}

export function normalizeVariableImportance(apiResponse) {
  const payload = apiResponse || {};
  const rawItems = Array.isArray(payload.items) ? payload.items : [];

  const items = rawItems
    .map((item) => {
      const feature = String(item?.feature ?? "").trim();
      const importance = Number(item?.importance ?? 0);
      if (!feature) return null;
      return {
        label: feature,
        value: Number.isNaN(importance) ? 0 : importance,
      };
    })
    .filter(Boolean)
    .sort((a, b) => b.value - a.value);

  return {
    source: payload.source || "fallback",
    items,
  };
}
