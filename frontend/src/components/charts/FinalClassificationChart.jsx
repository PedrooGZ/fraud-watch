import Card from "../ui/Card";
import { formatNumber } from "../../utils/formatters";

function getRowClass(label) {
  if (label === "Revisión") return "analysis-bar-fill review";
  if (label === "No revisión") return "analysis-bar-fill no-review";
  if (label === "Inválidas") return "analysis-bar-fill invalid";
  return "analysis-bar-fill";
}

export default function FinalClassificationChart({ data = [], loading = false, error = false }) {
  const safeData = Array.isArray(data) ? data : [];
  const hasData = safeData.length > 0;
  const maxValue = hasData ? Math.max(...safeData.map((item) => Number(item.value || 0)), 1) : 1;

  return (
    <Card className="analysis-chart-card">
      <div className="analysis-chart-header">
        <h3>Clasificación operativa</h3>
        <p>Resultado operativo del modelo</p>
      </div>

      <div className="analysis-chart-body">
        {loading ? <p className="notice">Cargando clasificación operativa...</p> : null}
        {error ? <p className="notice warn">No se pudo cargar la clasificación real. Mostrando datos de ejemplo.</p> : null}
        {!loading && !hasData ? (
          <div className="analysis-empty-state">
            <p className="notice">Aún no hay datos de clasificación disponibles.</p>
          </div>
        ) : null}

        {hasData ? (
          <div className="analysis-bar-list">
            {safeData.map((item) => {
              const value = Number(item.value || 0);
              const rawPct = maxValue > 0 ? (value / maxValue) * 100 : 0;
              const widthPct = value > 0 ? Math.min(92, Math.max(6, rawPct)) : 0;

              return (
                <article className="analysis-bar-row" key={item.label}>
                  <div className="analysis-bar-row-top">
                    <span className="analysis-bar-label">{item.label}</span>
                    <span className="analysis-bar-value">{formatNumber(value)}</span>
                  </div>
                  <div className="analysis-bar-track">
                    <div className={getRowClass(item.label)} style={{ width: `${widthPct}%` }} />
                  </div>
                </article>
              );
            })}
          </div>
        ) : null}
      </div>
    </Card>
  );
}
