import Card from "../ui/Card";
import { formatPercent } from "../../utils/formatters";

export default function VariableImportanceChart({
  data = [],
  source: _source = "fallback",
  loading = false,
  error = false,
}) {
  const safeData = Array.isArray(data) ? data : [];
  const hasData = safeData.length > 0;
  const maxValue = hasData ? Math.max(...safeData.map((item) => Number(item.value || 0)), 1) : 1;

  return (
    <Card className="analysis-chart-card">
      <div className="analysis-chart-header">
        <h3>Importancia de variables</h3>
      </div>

      <div className="analysis-chart-body">
        {loading ? <p className="notice">Cargando importancia de variables...</p> : null}
        {error ? <p className="notice warn">No se pudo cargar la importancia real. Mostrando datos de ejemplo.</p> : null}
        {!loading && !hasData ? (
          <div className="analysis-empty-state">
            <p className="notice">Aún no hay importancias de variables disponibles.</p>
          </div>
        ) : null}

        {hasData ? (
          <div className="analysis-chart-scroll-body">
            <div className="analysis-bar-list">
              {safeData.map((item) => {
                const normalized = Number(item.value || 0);
                const rawPct = maxValue > 0 ? (normalized / maxValue) * 100 : 0;
                const widthPct = normalized > 0 ? Math.min(92, Math.max(6, rawPct)) : 0;

                return (
                  <article className="analysis-bar-row" key={item.label}>
                    <div className="analysis-bar-row-top">
                      <span className="analysis-bar-label">{item.label}</span>
                      <span className="analysis-bar-value">{formatPercent(normalized * 100)}</span>
                    </div>
                    <div className="analysis-bar-track">
                      <div className="analysis-bar-fill" style={{ width: `${widthPct}%` }} />
                    </div>
                  </article>
                );
              })}
            </div>
          </div>
        ) : null}
      </div>
    </Card>
  );
}
