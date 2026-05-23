import { useCallback, useEffect, useMemo, useState } from "react";
import AppLayout from "../components/layout/AppLayout";
import PageHeader from "../components/layout/PageHeader";
import Card from "../components/ui/Card";
import ToggleButton from "../components/ui/ToggleButton";
import ReportHistoryTable from "../components/fraud/ReportHistoryTable";
import { api } from "../services/api";
import { normalizeReport } from "../utils/adapters";
import { formatReportDetailLevel, formatReportPeriod } from "../utils/formatters";

const PERIOD_OPTIONS = [
  { value: "today", label: "Hoy" },
  { value: "last_7_days", label: "7 días" },
  { value: "last_30_days", label: "30 días" },
  { value: "all", label: "Todo" },
];

const DETAIL_OPTIONS = [
  { value: "executive", label: "Ejecutivo" },
  { value: "operational", label: "Operativo" },
  { value: "complete", label: "Completo" },
];

const FORMAT_OPTIONS = [
  { value: "json", label: "JSON" },
  { value: "csv", label: "CSV" },
];

const SECTION_OPTIONS = [
  { value: "summary", label: "Resumen" },
  { value: "analytics", label: "Analítica" },
  { value: "drift", label: "Drift" },
  { value: "model", label: "Modelo" },
  { value: "policy_changes", label: "Cambios de política" },
  { value: "audit", label: "Auditoría" },
  { value: "batch_jobs", label: "Lotes" },
];

export default function ReportsPage() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [usingFallback, setUsingFallback] = useState(false);
  const [apiMessage, setApiMessage] = useState("");
  const [feedback, setFeedback] = useState({ type: "", text: "" });
  const [isGenerating, setIsGenerating] = useState(false);
  const [downloadingReportId, setDownloadingReportId] = useState(null);

  const [period, setPeriod] = useState("last_30_days");
  const [format, setFormat] = useState("json");
  const [detailLevel, setDetailLevel] = useState("executive");
  const [sections, setSections] = useState(["summary", "analytics", "drift", "model"]);

  const loadReports = useCallback(async () => {
    setLoading(true);
    setApiMessage("");
    try {
      const response = await api.getReports({ limit: 20, offset: 0 });
      const normalized = Array.isArray(response) ? response.map((item) => normalizeReport(item)) : [];
      setReports(normalized);
      setUsingFallback(false);
    } catch {
      setReports([]);
      setUsingFallback(true);
      setApiMessage("No se pudo conectar con la API. Mostrando datos de ejemplo.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadReports();
  }, [loadReports]);

  const selectedPeriodLabel = useMemo(() => formatReportPeriod(period), [period]);
  const selectedDetailLabel = useMemo(() => formatReportDetailLevel(detailLevel), [detailLevel]);

  const toggleSection = useCallback((sectionValue) => {
    setSections((prev) => (prev.includes(sectionValue)
      ? prev.filter((item) => item !== sectionValue)
      : [...prev, sectionValue]));
  }, []);

  const handleGenerateReport = useCallback(async () => {
    if (sections.length === 0) {
      setFeedback({ type: "error", text: "Debes seleccionar al menos una sección." });
      return;
    }

    setFeedback({ type: "", text: "" });
    setIsGenerating(true);

    try {
      await api.createReport({
        period,
        format,
        detail_level: detailLevel,
        sections,
      });
      setFeedback({ type: "success", text: "Informe generado correctamente." });
      await loadReports();
    } catch (error) {
      const detail = typeof error?.message === "string" && error.message.trim()
        ? error.message
        : "No se pudo generar el informe.";
      setFeedback({ type: "error", text: detail });
    } finally {
      setIsGenerating(false);
    }
  }, [detailLevel, format, loadReports, period, sections]);

  const handleDownloadReport = useCallback(async (report) => {
    if (!report?.id) {
      return;
    }

    setDownloadingReportId(report.id);
    setFeedback({ type: "", text: "" });
    try {
      await api.downloadReport(report.id);
      setFeedback({ type: "success", text: "Descarga iniciada." });
    } catch {
      setFeedback({ type: "error", text: "No se pudo descargar el informe." });
    } finally {
      setDownloadingReportId(null);
    }
  }, []);

  return (
    <AppLayout>
      <PageHeader
        title="Informes"
        subtitle="Generar reportes para dirección, riesgos y compliance."
        badge={`Periodo · ${selectedPeriodLabel}`}
        actionLabel={isGenerating ? "Generando..." : "Generar informe"}
        onAction={handleGenerateReport}
        actionDisabled={isGenerating || sections.length === 0}
      />

      {loading ? <p className="notice">Cargando informes...</p> : null}
      {apiMessage ? <p className="notice warn">{apiMessage}</p> : null}
      {feedback.text ? <p className={`notice ${feedback.type === "error" ? "error" : feedback.type === "success" ? "success" : ""}`.trim()}>{feedback.text}</p> : null}

      <Card>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10 }}>
          <h2 style={{ margin: 0 }}>Generador de informes</h2>
          <span className="badge">Guardado automático</span>
        </div>

        <Card style={{ marginTop: 12 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8 }}>
            <h3 style={{ marginTop: 0 }}>Periodo</h3>
            <strong>{selectedPeriodLabel}</strong>
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {PERIOD_OPTIONS.map((option) => (
              <ToggleButton
                key={option.value}
                active={period === option.value}
                onClick={() => setPeriod(option.value)}
              >
                {option.label}
              </ToggleButton>
            ))}
          </div>
        </Card>

        <div className="stats-grid" style={{ marginTop: 12 }}>
          <Card>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8 }}>
              <h3 style={{ marginTop: 0 }}>Formato</h3>
              <strong>{format.toUpperCase()}</strong>
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {FORMAT_OPTIONS.map((option) => (
                <ToggleButton
                  key={option.value}
                  active={format === option.value}
                  onClick={() => setFormat(option.value)}
                >
                  {option.label}
                </ToggleButton>
              ))}
            </div>
          </Card>

          <Card>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8 }}>
              <h3 style={{ marginTop: 0 }}>Nivel de detalle</h3>
              <strong>{selectedDetailLabel}</strong>
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {DETAIL_OPTIONS.map((option) => (
                <ToggleButton
                  key={option.value}
                  active={detailLevel === option.value}
                  onClick={() => setDetailLevel(option.value)}
                >
                  {option.label}
                </ToggleButton>
              ))}
            </div>
          </Card>
        </div>

        <Card style={{ marginTop: 12 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8 }}>
            <h3 style={{ marginTop: 0 }}>Secciones</h3>
            <strong>{sections.length} seleccionadas</strong>
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {SECTION_OPTIONS.map((option) => (
              <ToggleButton
                key={option.value}
                active={sections.includes(option.value)}
                onClick={() => toggleSection(option.value)}
              >
                {option.label}
              </ToggleButton>
            ))}
          </div>
        </Card>

        <div style={{ marginTop: 12 }}>
          <ReportHistoryTable
            reports={usingFallback ? null : reports}
            isFallback={usingFallback}
            emptyText="Aún no hay informes generados."
            onDownload={handleDownloadReport}
            downloadingReportId={downloadingReportId}
          />
        </div>
      </Card>
    </AppLayout>
  );
}
