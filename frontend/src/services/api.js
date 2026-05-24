const BASE_URL = import.meta.env.VITE_API_URL || "/api";
const AUTH_TOKEN_KEY = "fw_auth_token";
const AUTH_USER_KEY = "fw_auth_user";

export function setAuthToken(token) {
  if (!token) return;
  localStorage.setItem(AUTH_TOKEN_KEY, token);
}

export function getAuthToken() {
  return localStorage.getItem(AUTH_TOKEN_KEY);
}

export function clearAuthToken() {
  localStorage.removeItem(AUTH_TOKEN_KEY);
}

export function setStoredUser(user) {
  if (!user) return;
  localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
}

export function getStoredUser() {
  const raw = localStorage.getItem(AUTH_USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function clearStoredUser() {
  localStorage.removeItem(AUTH_USER_KEY);
}

function buildQuery(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") return;
    query.set(key, String(value));
  });
  const queryString = query.toString();
  return queryString ? `?${queryString}` : "";
}

async function request(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  const token = getAuthToken();
  if (token && !headers.Authorization) {
    headers.Authorization = `Bearer ${token}`;
  }
  if (options.body && !(options.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(`${BASE_URL}${path}`, {
    headers,
    ...options,
  });

  if (!response.ok) {
    let message = "No se pudo completar la solicitud.";
    try {
      const body = await response.json();
      if (typeof body?.detail === "string" && body.detail.trim()) {
        message = body.detail;
      }
    } catch {
      // keep generic message
    }
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }

  return response.json();
}

async function requestBlob(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  const token = getAuthToken();
  if (token && !headers.Authorization) {
    headers.Authorization = `Bearer ${token}`;
  }
  const response = await fetch(`${BASE_URL}${path}`, {
    headers,
    ...options,
  });

  if (!response.ok) {
    let message = "No se pudo completar la solicitud.";
    try {
      const body = await response.json();
      if (typeof body?.detail === "string" && body.detail.trim()) {
        message = body.detail;
      }
    } catch {
      // keep generic message
    }
    const error = new Error(message);
    error.status = response.status;
    throw error;
  }

  return {
    blob: await response.blob(),
    headers: response.headers,
  };
}

export const getHealth = () => request("/health");
export const register = (payload) => request("/auth/register", { method: "POST", body: JSON.stringify(payload) });
export const login = (payload) => request("/auth/login", { method: "POST", body: JSON.stringify(payload) });
export const getMe = () => request("/auth/me");
export const getPolicy = () => request("/policy");
export const updatePolicy = (payload) => request("/policy", { method: "PUT", body: JSON.stringify(payload) });
export const getPolicyHistory = (params = {}) => request(`/policy/history${buildQuery(params)}`);
export const getBatchJobs = (params = {}) => request(`/batch-jobs${buildQuery(params)}`);
export const getPredictions = (params = {}) => request(`/predictions${buildQuery(params)}`);
export const getDashboardSummary = () => request("/dashboard/summary");
export const getDashboardPriorityCases = (params = {}) => request(`/dashboard/priority-cases${buildQuery(params)}`);
export const getAuditEvents = (params = {}) => request(`/audit-events${buildQuery(params)}`);
export const getActiveModelVersion = () => request("/model-versions/active");
export const getReports = (params = {}) => request(`/reports${buildQuery(params)}`);
export const createReport = (payload) => request("/reports", { method: "POST", body: JSON.stringify(payload) });
export const getReportById = (reportId) => request(`/reports/${reportId}`);
export const getDriftRuns = (params = {}) => request(`/drift-runs${buildQuery(params)}`);
export const getFraudEvolution = (params = {}) => request(`/analytics/fraud-evolution${buildQuery(params)}`);
export const getRiskDistribution = () => request("/analytics/risk-distribution");
export const getClassificationSummary = () => request("/analytics/classification-summary");
export const getVariableImportance = (params = {}) => request(`/analytics/variable-importance${buildQuery(params)}`);
export const predict = (payload) => request("/predict", { method: "POST", body: JSON.stringify(payload) });
export const predictBatch = (payload) => request("/predict_batch", { method: "POST", body: JSON.stringify(payload) });
export const uploadBatchCsv = (file) => {
  const formData = new FormData();
  formData.append("file", file);
  return request("/batch-jobs/upload", { method: "POST", body: formData });
};
export const downloadBatchResults = (batchJobId) =>
  requestBlob(`/batch-jobs/${batchJobId}/download`, { method: "GET" });
export const downloadReport = async (reportId) => {
  const { blob, headers } = await requestBlob(`/reports/${reportId}/download`, { method: "GET" });
  const contentDisposition = headers.get("content-disposition") || "";
  const contentType = (headers.get("content-type") || "").toLowerCase();
  const fileNameMatch = contentDisposition.match(/filename\*?=(?:UTF-8''|")?([^\";]+)/i);
  const fallbackExtension = contentType.includes("text/csv")
    ? "csv"
    : contentType.includes("application/json")
      ? "json"
      : "dat";
  const fallbackName = `report_${reportId}.${fallbackExtension}`;
  const fileName = fileNameMatch?.[1] ? decodeURIComponent(fileNameMatch[1].replace(/"/g, "")) : fallbackName;

  const blobUrl = window.URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = blobUrl;
  anchor.download = fileName;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  window.URL.revokeObjectURL(blobUrl);
};

export const api = {
  getHealth,
  register,
  login,
  getMe,
  getPolicy,
  updatePolicy,
  getPolicyHistory,
  getBatchJobs,
  getPredictions,
  getDashboardSummary,
  getDashboardPriorityCases,
  getAuditEvents,
  getActiveModelVersion,
  getReports,
  createReport,
  getReportById,
  getDriftRuns,
  getFraudEvolution,
  getRiskDistribution,
  getClassificationSummary,
  getVariableImportance,
  predict,
  predictBatch,
  uploadBatchCsv,
  downloadBatchResults,
  downloadReport,
};

export default api;
