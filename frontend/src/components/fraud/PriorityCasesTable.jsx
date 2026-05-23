import { priorityCases as mockPriorityCases } from "../../data/mockData";
import Badge from "../ui/Badge";
import Card from "../ui/Card";

export default function PriorityCasesTable({
  rows = null,
  isFallback = false,
  emptyText = "No hay casos en revisión actualmente.",
}) {
  const hasRows = Array.isArray(rows) && rows.length > 0;
  const cases = hasRows ? rows : isFallback ? mockPriorityCases : [];

  return (
    <Card className="dashboard-scroll-card">
      <div
        className="dashboard-scroll-header"
        style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10, gap: 10 }}
      >
        <h3 style={{ margin: 0 }}>Casos prioritarios</h3>
        <Badge>{hasRows ? `Top ${cases.length}` : "Top 10"}</Badge>
      </div>

      <div className="dashboard-scroll-body">
        {isFallback ? <p className="notice warn">No se pudo conectar con la API. Mostrando datos de ejemplo.</p> : null}
        {!hasRows && !isFallback ? <p className="notice">{emptyText}</p> : null}

        <div className="table-like">
          {cases.map((row) => (
            <article className="data-card" key={row.id}>
              {"client" in row ? (
                <>
                  <div className="data-row"><strong>ID</strong><span>{row.id}</span></div>
                  <div className="data-row"><strong>Cliente</strong><span>{row.client}</span></div>
                  <div className="data-row"><strong>Importe</strong><span>{row.amount}</span></div>
                  <div className="data-row"><strong>Riesgo</strong><span>{row.risk}</span></div>
                </>
              ) : (
                <>
                  <div className="data-row"><strong>ID predicción</strong><span>{row.id}</span></div>
                  <div className="data-row"><strong>Lote</strong><span>{row.batch_job_id ?? "N/A"}</span></div>
                  <div className="data-row"><strong>Probabilidad</strong><span>{row.proba_fraud_label}</span></div>
                  <div className="data-row"><strong>Estado</strong><span>{row.review_label}</span></div>
                  <div className="data-row"><strong>Validez</strong><span>{row.is_valid_label}</span></div>
                  <div className="data-row"><strong>Fecha</strong><span>{row.created_at_label}</span></div>
                </>
              )}
            </article>
          ))}
        </div>
      </div>
    </Card>
  );
}

