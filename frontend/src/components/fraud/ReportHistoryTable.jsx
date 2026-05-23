import { reportHistory as mockReportHistory } from "../../data/mockData";
import Button from "../ui/Button";
import Card from "../ui/Card";

export default function ReportHistoryTable({
  reports = null,
  isFallback = false,
  emptyText = "Aún no hay informes generados.",
  onDownload = null,
  downloadingReportId = null,
}) {
  const hasReports = Array.isArray(reports) && reports.length > 0;
  const rows = hasReports ? reports : isFallback ? mockReportHistory : [];

  return (
    <Card className="dashboard-scroll-card">
      <div className="dashboard-scroll-header">
        <h3 className="section-title">Historial de informes</h3>
      </div>
      <div className="dashboard-scroll-body">
        {isFallback ? <p className="notice warn">No se pudo conectar con la API. Mostrando datos de ejemplo.</p> : null}
        {!hasReports && !isFallback ? <p className="notice">{emptyText}</p> : null}
        <div className="history-table">
        {rows.map((report) => {
          const isMock = "date" in report;
          const canDownload = !isMock && !isFallback && typeof onDownload === "function" && !!report?.id && !!report?.file_path;
          const isDownloading = downloadingReportId === report.id;

          return (
            <article className="data-card" key={report.id || report.report_code}>
              {isMock ? (
                <>
                  <div className="data-row"><strong>Fecha</strong><span>{report.date}</span></div>
                  <div className="data-row"><strong>ID</strong><span>{report.id}</span></div>
                  <div className="data-row"><strong>Periodo</strong><span>{report.period}</span></div>
                  <div className="data-row"><strong>Formato</strong><span>{report.format}</span></div>
                  <div className="data-row"><strong>Generado por</strong><span>{report.generatedBy}</span></div>
                </>
              ) : (
                <>
                  <div className="data-row"><strong>Fecha</strong><span>{report.created_at_label}</span></div>
                  <div className="data-row"><strong>ID</strong><span>{report.report_code}</span></div>
                  <div className="data-row"><strong>Periodo</strong><span>{report.period_label || report.period}</span></div>
                  <div className="data-row"><strong>Formato</strong><span>{report.format_label || report.format}</span></div>
                  <div className="data-row"><strong>Detalle</strong><span>{report.detail_level_label || report.detail_level}</span></div>
                  <div style={{ marginTop: 10 }}>
                    <Button
                      variant="primary"
                      block
                      onClick={() => onDownload?.(report)}
                      disabled={!canDownload || isDownloading}
                    >
                      {isDownloading ? "Descargando..." : "Descargar"}
                    </Button>
                  </div>
                </>
              )}
            </article>
          );
        })}
        </div>
      </div>
    </Card>
  );
}
