import Card from "../ui/Card";
import ToggleButton from "../ui/ToggleButton";
import { formatDate } from "../../utils/formatters";

const PRIORITY_OPTIONS = [
  { value: "risk", label: "Riesgo" },
  { value: "impact", label: "Impacto €" },
  { value: "mixed", label: "Mixto" },
];

const ERROR_OPTIONS = [
  { value: "balanced", label: "Equilibrado" },
  { value: "reduce_fp", label: "Reducir FP" },
  { value: "reduce_fn", label: "Reducir FN" },
];

const PRIORITY_LABEL = {
  risk: "Riesgo",
  impact: "Impacto",
  mixed: "Mixto",
};

const ERROR_LABEL = {
  balanced: "Equilibrado",
  reduce_fp: "Reducir falsos positivos",
  reduce_fn: "Reducir falsos negativos",
};

function toSafeInteger(value) {
  const numeric = Number(value);
  if (Number.isNaN(numeric)) return 0;
  return Math.max(0, Math.trunc(numeric));
}

export default function PolicySettingsPanel({
  value,
  onChange,
  changeReason = "",
  onChangeReason,
  loading = false,
  saving = false,
  saveMessage = "",
  saveMessageType = "",
  usingFallback = false,
  history = [],
  historyLoading = false,
  historyError = false,
  canEdit = true,
  currentUserRole = "",
}) {
  const controlsDisabled = loading || saving || !canEdit;
  const policy = {
    threshold_cost: Number(value?.threshold_cost ?? 0.02),
    max_alerts: toSafeInteger(value?.max_alerts ?? 500),
    priority_mode: value?.priority_mode ?? "risk",
    error_cost_mode: value?.error_cost_mode ?? "balanced",
  };

  const update = (patch) => {
    if (!onChange || controlsDisabled) return;
    onChange({ ...policy, ...patch });
  };

  return (
    <Card>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10 }}>
        <h3 style={{ margin: 0 }}>Política de revisión</h3>
        <span className="badge">{saving ? "Guardando..." : "Política activa"}</span>
      </div>

      {usingFallback ? <p className="notice warn" style={{ marginTop: 12 }}>No se pudo conectar con la API. Mostrando datos de ejemplo.</p> : null}
      {!canEdit ? (
        <p className="notice warn" style={{ marginTop: 12 }}>
          Solo un administrador puede modificar la política de revisión. Puedes consultar la configuración y el histórico.
        </p>
      ) : null}
      {saveMessage ? <p className={`notice ${saveMessageType}`.trim()} style={{ marginTop: 12 }}>{saveMessage}</p> : null}

      <Card style={{ marginTop: 12 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10 }}>
          <span>Umbral de detección</span>
          <strong>{policy.threshold_cost.toFixed(2)}</strong>
        </div>
        <input
          type="range"
          min="0"
          max="1"
          step="0.01"
          value={policy.threshold_cost}
          onChange={(e) => update({ threshold_cost: Number(e.target.value) })}
          style={{ width: "100%", marginTop: 8 }}
          disabled={controlsDisabled}
        />
        <div style={{ marginTop: 10, display: "flex", justifyContent: "space-between", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
          <label className="input-wrap" style={{ maxWidth: 180 }}>
            <span>Valor exacto</span>
            <input
              className="input"
              type="number"
              min="0"
              max="1"
              step="0.01"
              value={policy.threshold_cost}
              onChange={(e) => update({ threshold_cost: Number(e.target.value) })}
              disabled={controlsDisabled}
            />
          </label>
        </div>
        <p style={{ marginBottom: 0, color: "var(--text-soft)" }}>Más alto = menos alertas · riesgo de más FN</p>
      </Card>

      <div className="stats-grid" style={{ marginTop: 12 }}>
        <Card>
          <h4 style={{ marginTop: 0 }}>Capacidad diaria</h4>
          <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
            <ToggleButton
              onClick={() => update({ max_alerts: Math.max(0, policy.max_alerts - 1) })}
              disabled={controlsDisabled}
            >
              -
            </ToggleButton>
            <span className="badge">Capacidad actual: {policy.max_alerts}</span>
            <ToggleButton
              onClick={() => update({ max_alerts: policy.max_alerts + 1 })}
              disabled={controlsDisabled}
            >
              +
            </ToggleButton>
          </div>
          <p style={{ marginBottom: 0, color: "var(--text-soft)" }}>Limita el volumen revisable</p>
        </Card>

        <Card>
          <h4 style={{ marginTop: 0 }}>Priorizar por</h4>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            {PRIORITY_OPTIONS.map((option) => (
              <ToggleButton
                key={option.value}
                active={policy.priority_mode === option.value}
                onClick={() => update({ priority_mode: option.value })}
                disabled={controlsDisabled}
              >
                {option.label}
              </ToggleButton>
            ))}
          </div>
          <p style={{ marginBottom: 0, color: "var(--text-soft)" }}>Criterio de orden en la cola</p>
        </Card>
      </div>

      <Card style={{ marginTop: 12 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10 }}>
          <h4 style={{ marginTop: 0 }}>Coste de errores</h4>
          <strong>{ERROR_LABEL[policy.error_cost_mode] || "Equilibrado"}</strong>
        </div>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          {ERROR_OPTIONS.map((option) => (
            <ToggleButton
              key={option.value}
              active={policy.error_cost_mode === option.value}
              onClick={() => update({ error_cost_mode: option.value })}
              disabled={controlsDisabled}
            >
              {option.label}
            </ToggleButton>
          ))}
        </div>
        <p style={{ marginBottom: 0, color: "var(--text-soft)" }}>Ajusta según política de riesgo</p>
      </Card>

      <Card style={{ marginTop: 12 }}>
        <h4 style={{ marginTop: 0 }}>Motivo del cambio</h4>
        <label className="input-wrap">
          <span>Motivo del cambio (opcional)</span>
          <input
            className="input"
            type="text"
            placeholder="Ej: Ajuste tras revisión semanal"
            value={changeReason}
            onChange={(e) => onChangeReason?.(e.target.value)}
            disabled={controlsDisabled}
          />
        </label>
        {!canEdit && currentUserRole ? (
          <p style={{ marginBottom: 0, color: "var(--text-soft)" }}>
            Rol actual: {currentUserRole}
          </p>
        ) : null}
      </Card>

      <Card className="dashboard-scroll-card" style={{ marginTop: 12 }}>
        <div
          className="dashboard-scroll-header"
          style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10 }}
        >
          <h4 style={{ margin: 0 }}>Últimos cambios de política</h4>
          <span className="badge">{historyLoading ? "Cargando..." : `Registros: ${history.length}`}</span>
        </div>

        <div className="dashboard-scroll-body" style={{ marginTop: 12 }}>
          {historyError ? <p className="notice warn">No se pudo cargar el historial de política.</p> : null}

          {!historyLoading && !historyError && history.length === 0 ? (
            <p className="notice">No hay registros disponibles todavía.</p>
          ) : null}

          <div className="history-table">
            {history.map((item) => (
              <article key={item.id} className="data-card">
                <div className="data-row"><strong>Fecha</strong><span>{formatDate(item.created_at)}</span></div>
                <div className="data-row"><strong>Umbral</strong><span>{item.new_values_json?.threshold_cost ?? "—"}</span></div>
                <div className="data-row"><strong>Capacidad</strong><span>{item.new_values_json?.max_alerts ?? "—"}</span></div>
                <div className="data-row"><strong>Prioridad</strong><span>{PRIORITY_LABEL[item.new_values_json?.priority_mode] || "—"}</span></div>
                <div className="data-row"><strong>Coste de errores</strong><span>{ERROR_LABEL[item.new_values_json?.error_cost_mode] || "—"}</span></div>
                <div className="data-row"><strong>Motivo</strong><span>{item.reason || "—"}</span></div>
              </article>
            ))}
          </div>
        </div>
      </Card>
    </Card>
  );
}
