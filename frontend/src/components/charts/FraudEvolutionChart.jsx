import Card from "../ui/Card";
import { formatNumber } from "../../utils/formatters";

export default function FraudEvolutionChart({ data = [], loading = false, error = false }) {
  const hasData = Array.isArray(data) && data.length > 0;
  const maxTotal = hasData ? Math.max(...data.map((item) => Number(item.total || 0)), 1) : 1;

  return (
    <Card className="analysis-chart-card">
      <div className="analysis-chart-header">
        <h3>Evolución de alertas</h3>
        <p>Predicciones y casos en revisión por periodo</p>
      </div>

      <div className="analysis-chart-body">
        {loading ? <p className="notice">Cargando evolución...</p> : null}
        {error ? <p className="notice warn">No se pudo cargar la evolución real. Mostrando datos de ejemplo.</p> : null}
        {!loading && !hasData ? (
          <div className="analysis-empty-state">
            <p className="notice">Aún no hay datos de evolución disponibles.</p>
          </div>
        ) : null}

        {hasData ? (
          <div className="analysis-evolution-plot">
            {data.map((item, index) => {
              const total = Number(item.total || 0);
              const review = Number(item.review || 0);
              const invalid = Number(item.invalid || 0);
              const rawHeight = maxTotal > 0 ? (total / maxTotal) * 100 : 0;
              const barHeight = total > 0 ? Math.min(82, Math.max(8, rawHeight)) : 0;

              return (
                <div key={`${item.label}-${index}`} className="analysis-evolution-col">
                  <div className="analysis-evolution-bar-wrap">
                    <div className="analysis-evolution-bar" style={{ height: `${barHeight}%` }} />
                  </div>
                  <div className="analysis-evolution-meta">
                    <div>{item.label}</div>
                    <div>T: {formatNumber(total)}</div>
                    <div>R: {formatNumber(review)} · I: {formatNumber(invalid)}</div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : null}
      </div>
    </Card>
  );
}
