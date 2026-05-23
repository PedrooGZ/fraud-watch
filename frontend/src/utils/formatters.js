export function formatDate(value) {
  if (!value) return "N/A";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "N/A";
  return date.toLocaleString("es-ES", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatDateShort(value) {
  if (!value) return "N/A";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "N/A";
  return date.toLocaleDateString("es-ES", {
    day: "2-digit",
    month: "2-digit",
  });
}

export function formatNumber(value) {
  const numericValue = Number(value);
  if (Number.isNaN(numericValue)) return "0";
  return numericValue.toLocaleString("es-ES");
}

export function formatPercent(value) {
  const numericValue = Number(value);
  if (Number.isNaN(numericValue)) return "0%";
  return `${numericValue.toFixed(1)}%`;
}

export function formatProbability(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "N/A";
  const numericValue = Number(value);
  const probability = numericValue <= 1 ? numericValue * 100 : numericValue;
  return `${probability.toFixed(2)}%`;
}

export function toBooleanFlag(value) {
  if (typeof value === "boolean") return value;
  if (typeof value === "number") return value === 1;
  if (typeof value === "string") {
    const normalized = value.trim().toLowerCase();
    if (normalized === "1" || normalized === "true") return true;
    if (normalized === "0" || normalized === "false" || normalized === "") return false;
  }
  return false;
}

export function formatBooleanReview(value) {
  return toBooleanFlag(value) ? "Revisión" : "No revisión";
}

export function formatValidity(value) {
  return toBooleanFlag(value) ? "Válida" : "Inválida";
}

export function formatReportPeriod(period) {
  const mapping = {
    today: "Hoy",
    last_7_days: "Últimos 7 días",
    last_30_days: "Últimos 30 días",
    all: "Todo",
  };
  return mapping[period] || period || "N/A";
}

export function formatReportFormat(format) {
  const mapping = {
    json: "JSON",
    csv: "CSV",
    pdf: "PDF",
  };
  return mapping[String(format || "").toLowerCase()] || (format ? String(format).toUpperCase() : "N/A");
}

export function formatReportDetailLevel(detailLevel) {
  const mapping = {
    executive: "Ejecutivo",
    operational: "Operativo",
    complete: "Completo",
  };
  return mapping[detailLevel] || detailLevel || "N/A";
}
