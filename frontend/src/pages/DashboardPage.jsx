import { useCallback, useEffect, useMemo, useState } from "react";
import AppLayout from "../components/layout/AppLayout";
import PageHeader from "../components/layout/PageHeader";
import StatCard from "../components/ui/StatCard";
import Card from "../components/ui/Card";
import PriorityCasesTable from "../components/fraud/PriorityCasesTable";
import CsvUploadModal from "../components/fraud/CsvUploadModal";
import { dashboardStats } from "../data/mockData";
import { api } from "../services/api";
import {
  normalizeBatchJob,
  normalizeDashboardPriorityCase,
  normalizeDashboardSummary,
} from "../utils/adapters";
import { formatDate } from "../utils/formatters";

function buildStats(summary) {
  if (!summary) return dashboardStats;

  const activeModel = summary.active_model;
  const activePolicy = summary.active_policy;

  return [
    {
      title: "Predicciones totales",
      value: String(summary.total_predictions),
      badge: "Operación actual",
      footer: `Predicciones recientes (24h): ${summary.recent_predictions}`,
    },
    {
      title: "Alertas generadas",
      value: String(summary.review_count),
      badge: summary.review_count > 0 ? "En revisión" : "Sin revisión",
      footer: `Casos válidos: ${summary.valid_predictions}`,
    },
    {
      title: "Registros inválidos",
      value: String(summary.invalid_predictions),
      badge: summary.invalid_predictions > 0 ? "Revisar datos" : "Controlado",
      footer: "Errores de validación detectados",
    },
    {
      title: "Lotes completados",
      value: String(summary.completed_batch_jobs),
      badge: `${summary.failed_batch_jobs} fallidos`,
      footer: `Total lotes: ${summary.batch_jobs_count}`,
    },
    {
      title: "Modelo activo",
      value: activeModel ? activeModel.name : "N/A",
      badge: activeModel ? activeModel.model_type : "Sin modelo activo",
      footer: activeModel?.created_at_label ? `Activado: ${activeModel.created_at_label}` : "Sin fecha de activación",
    },
    {
      title: "Política activa",
      value: activePolicy ? `Umbral ${activePolicy.threshold_cost}` : "N/A",
      badge: activePolicy ? activePolicy.priority_mode : "Sin política",
      footer: activePolicy ? `Max alerts: ${activePolicy.max_alerts}` : "Sin configuración activa",
    },
  ];
}

export default function DashboardPage() {
  const [openCsv, setOpenCsv] = useState(false);
  const [stats, setStats] = useState(dashboardStats);
  const [priorityRows, setPriorityRows] = useState([]);
  const [batchJobs, setBatchJobs] = useState([]);
  const [auditEvents, setAuditEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [priorityFallback, setPriorityFallback] = useState(false);
  const [apiWarning, setApiWarning] = useState("");

  const pageBadge = useMemo(() => {
    const dateLabel = new Date().toLocaleDateString("es-ES", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
    return `Hoy · ${dateLabel}`;
  }, []);

  const loadDashboardData = useCallback(async () => {
    setLoading(true);
    setApiWarning("");

    const [summaryResult, priorityResult, batchJobsResult, auditEventsResult] = await Promise.allSettled([
      api.getDashboardSummary(),
      api.getDashboardPriorityCases({ limit: 10, offset: 0, only_review: false }),
      api.getBatchJobs({ limit: 20, offset: 0, order: "desc" }),
      api.getAuditEvents({ limit: 5, offset: 0 }),
    ]);

    const outcomes = [summaryResult, priorityResult, batchJobsResult, auditEventsResult];
    const hasAnySuccess = outcomes.some((outcome) => outcome.status === "fulfilled");

    if (!hasAnySuccess) {
      setStats(dashboardStats);
      setPriorityRows([]);
      setPriorityFallback(true);
      setBatchJobs([]);
      setAuditEvents([]);
      setApiWarning("No se pudo conectar con la API. Mostrando datos de ejemplo.");
      setLoading(false);
      return;
    }

    const warningMessages = [];

    if (summaryResult.status === "fulfilled") {
      const summary = normalizeDashboardSummary(summaryResult.value);
      setStats(buildStats(summary));
    } else {
      setStats(dashboardStats);
      warningMessages.push("No se pudo cargar el resumen de dashboard. Mostrando métricas de ejemplo.");
    }

    if (priorityResult.status === "fulfilled") {
      const rows = Array.isArray(priorityResult.value)
        ? priorityResult.value.map((item) => normalizeDashboardPriorityCase(item))
        : [];
      setPriorityRows(rows);
      setPriorityFallback(false);
    } else {
      setPriorityRows([]);
      setPriorityFallback(true);
      warningMessages.push("No se pudieron cargar los casos prioritarios. Mostrando datos de ejemplo.");
    }

    if (batchJobsResult.status === "fulfilled") {
      const normalizedBatchJobs = Array.isArray(batchJobsResult.value)
        ? batchJobsResult.value.map((item) => normalizeBatchJob(item))
        : [];
      setBatchJobs(normalizedBatchJobs.slice(0, 5));
    } else {
      setBatchJobs([]);
      warningMessages.push("No se pudieron cargar los lotes recientes.");
    }

    if (auditEventsResult.status === "fulfilled") {
      const normalizedAuditEvents = Array.isArray(auditEventsResult.value) ? auditEventsResult.value : [];
      setAuditEvents(normalizedAuditEvents);
    } else {
      setAuditEvents([]);
      warningMessages.push("No se pudo cargar la auditoría reciente.");
    }

    if (warningMessages.length > 0) {
      setApiWarning(warningMessages.join(" "));
    }

    setLoading(false);
  }, []);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  const handleUploadSuccess = useCallback(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  return (
    <AppLayout>
      <PageHeader
        title="Dashboard"
        subtitle="Resumen operativo del día."
        badge={pageBadge}
        actionLabel="Subir CSV"
        onAction={() => setOpenCsv(true)}
      />

      {loading ? <p className="notice">Cargando datos del dashboard...</p> : null}
      {apiWarning ? <p className="notice warn">{apiWarning}</p> : null}

      <section className="stats-grid">
        {stats.map((item) => <StatCard key={item.title} {...item} />)}
      </section>

      <div style={{ marginTop: 16 }}>
        <PriorityCasesTable
          rows={priorityFallback ? null : priorityRows}
          isFallback={priorityFallback}
          emptyText="No hay casos prioritarios disponibles actualmente."
        />
      </div>

      <div className="stats-grid" style={{ marginTop: 16 }}>
        <Card className="dashboard-scroll-card">
          <div className="dashboard-scroll-header">
            <h3 className="section-title">Batch jobs recientes</h3>
          </div>
          <div className="dashboard-scroll-body">
            {batchJobs.length === 0 ? (
              <p className="notice">No hay registros disponibles todavía.</p>
            ) : (
              <div className="table-like">
                {batchJobs.map((job) => (
                  <article className="data-card" key={job.id}>
                    <div className="data-row"><strong>ID</strong><span>{job.id}</span></div>
                    <div className="data-row"><strong>Archivo</strong><span>{job.filename}</span></div>
                    <div className="data-row"><strong>Status</strong><span>{job.status}</span></div>
                    <div className="data-row"><strong>Filas</strong><span>{job.valid_rows}/{job.total_rows}</span></div>
                    <div className="data-row"><strong>Creado</strong><span>{job.created_at_label}</span></div>
                  </article>
                ))}
              </div>
            )}
          </div>
        </Card>

        <Card className="dashboard-scroll-card">
          <div className="dashboard-scroll-header">
            <h3 className="section-title">Auditoría reciente</h3>
          </div>
          <div className="dashboard-scroll-body">
            {auditEvents.length === 0 ? (
              <p className="notice">No hay registros disponibles todavía.</p>
            ) : (
              <div className="table-like">
                {auditEvents.map((event) => (
                  <article className="data-card" key={event.id}>
                    <div className="data-row"><strong>Evento</strong><span>{event.event_type}</span></div>
                    <div className="data-row"><strong>Entidad</strong><span>{event.entity_type || "N/A"}</span></div>
                    <div className="data-row"><strong>ID entidad</strong><span>{event.entity_id || "N/A"}</span></div>
                    <div className="data-row"><strong>Fecha</strong><span>{formatDate(event.created_at)}</span></div>
                  </article>
                ))}
              </div>
            )}
          </div>
        </Card>
      </div>

      <CsvUploadModal
        open={openCsv}
        onClose={() => setOpenCsv(false)}
        onUploadSuccess={handleUploadSuccess}
      />
    </AppLayout>
  );
}
