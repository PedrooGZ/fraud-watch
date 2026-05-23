import Card from "../ui/Card";
import { formatNumber, formatPercent } from "../../utils/formatters";

export default function RiskDonutChart({ data = [], loading = false, error = false }) {
  const safeData = Array.isArray(data) ? data : [];
  const low = Number(safeData.find((item) => item.label === "Bajo")?.value ?? 0);
  const medium = Number(safeData.find((item) => item.label === "Medio")?.value ?? 0);
  const high = Number(safeData.find((item) => item.label === "Alto")?.value ?? 0);
  const total = low + medium + high;

  const lowPct = total > 0 ? (low / total) * 100 : 0;
  const mediumPct = total > 0 ? (medium / total) * 100 : 0;
  const highPct = total > 0 ? (high / total) * 100 : 0;

  return (
    <Card className="analysis-chart-card">
      <div className="analysis-chart-header">
        <h3>Distribución del riesgo</h3>
        <p>Score entre 0 y 1</p>
      </div>

      <div className="analysis-chart-body">
        {loading ? <p className="notice">Cargando distribución de riesgo...</p> : null}
        {error ? <p className="notice warn">No se pudo cargar la distribución real. Mostrando datos de ejemplo.</p> : null}
        {!loading && total === 0 ? (
          <div className="analysis-empty-state">
            <p className="notice">Aún no hay predicciones válidas para calcular distribución de riesgo.</p>
          </div>
        ) : null}

        {total > 0 ? (
          <div className="analysis-donut-shell">
            <div
              style={{
                width: 150,
                height: 150,
                borderRadius: "50%",
                background: `conic-gradient(#2bb24c 0 ${lowPct + mediumPct}%, #eb5543 ${lowPct + mediumPct}% 100%)`,
                position: "relative",
              }}
            >
              <div
                style={{
                  position: "absolute",
                  inset: 28,
                  borderRadius: "50%",
                  background: "#182238",
                  display: "grid",
                  placeItems: "center",
                  color: "var(--text-soft)",
                  fontSize: 12,
                  textAlign: "center",
                  padding: 6,
                }}
              >
                Total<br />{formatNumber(total)}
              </div>
            </div>

            <div className="analysis-donut-legend">
              <div><span>Bajo</span><span>{formatPercent(lowPct)} ({formatNumber(low)})</span></div>
              <div><span>Medio</span><span>{formatPercent(mediumPct)} ({formatNumber(medium)})</span></div>
              <div><span>Alto</span><span>{formatPercent(highPct)} ({formatNumber(high)})</span></div>
            </div>
          </div>
        ) : null}
      </div>
    </Card>
  );
}
