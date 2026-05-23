import { useCallback, useEffect, useState } from "react";
import AppLayout from "../components/layout/AppLayout";
import PageHeader from "../components/layout/PageHeader";
import Card from "../components/ui/Card";
import FraudEvolutionChart from "../components/charts/FraudEvolutionChart";
import RiskDonutChart from "../components/charts/RiskDonutChart";
import FinalClassificationChart from "../components/charts/FinalClassificationChart";
import VariableImportanceChart from "../components/charts/VariableImportanceChart";
import { api } from "../services/api";
import { chartData } from "../data/mockData";
import {
  normalizeClassificationSummary,
  normalizeDriftRun,
  normalizeFraudEvolution,
  normalizeRiskDistribution,
  normalizeVariableImportance,
} from "../utils/adapters";
import { formatDate } from "../utils/formatters";

function buildMockFraudEvolution() {
  return chartData.evolution.map((value, index) => {
    const total = Number(value) || 0;
    const review = Math.max(0, Math.round(total * 0.22));
    const invalid = Math.max(0, Math.round(total * 0.06));
    return {
      label: `D${index + 1}`,
      total,
      review,
      invalid,
      date: null,
    };
  });
}

function buildMockRiskDistribution() {
  const [low = 0, medium = 0, high = 0] = chartData.donut || [];
  return [
    { label: "Bajo", value: Number(low) || 0 },
    { label: "Medio", value: Number(medium) || 0 },
    { label: "Alto", value: Number(high) || 0 },
  ];
}

function buildMockClassificationSummary() {
  const review = Number(chartData.classification?.review ?? 0);
  const noReview = Number(chartData.classification?.noReview ?? 0);
  return [
    { label: "Revisión", value: Number.isNaN(review) ? 0 : review },
    { label: "No revisión", value: Number.isNaN(noReview) ? 0 : noReview },
    { label: "Inválidas", value: 0 },
  ];
}

function buildMockVariableImportance() {
  return {
    source: "mock",
    items: Array.isArray(chartData.importance)
      ? chartData.importance.map((item) => ({
        label: item.label,
        value: Number(item.value ?? 0),
      }))
      : [],
  };
}

export default function VisualAnalysisPage() {
  const [driftRuns, setDriftRuns] = useState([]);
  const [activeModel, setActiveModel] = useState(null);
  const [loading, setLoading] = useState(true);
  const [apiMessage, setApiMessage] = useState("");

  const [fraudEvolutionData, setFraudEvolutionData] = useState([]);
  const [riskDistributionData, setRiskDistributionData] = useState([]);
  const [classificationData, setClassificationData] = useState([]);
  const [variableImportanceData, setVariableImportanceData] = useState({ source: "fallback", items: [] });

  const [fraudEvolutionError, setFraudEvolutionError] = useState(false);
  const [riskDistributionError, setRiskDistributionError] = useState(false);
  const [classificationError, setClassificationError] = useState(false);
  const [variableImportanceError, setVariableImportanceError] = useState(false);

  const loadAnalysisData = useCallback(async () => {
    setLoading(true);
    setApiMessage("");

    const [
      driftRunsResult,
      activeModelResult,
      fraudEvolutionResult,
      riskDistributionResult,
      classificationSummaryResult,
      variableImportanceResult,
    ] = await Promise.allSettled([
      api.getDriftRuns({ limit: 20, offset: 0 }),
      api.getActiveModelVersion(),
      api.getFraudEvolution({ days: 30 }),
      api.getRiskDistribution(),
      api.getClassificationSummary(),
      api.getVariableImportance({ limit: 10 }),
    ]);

    const messages = [];
    let usedFallbackForAnalytics = false;

    if (driftRunsResult.status === "fulfilled" && Array.isArray(driftRunsResult.value)) {
      setDriftRuns(driftRunsResult.value.map((item) => normalizeDriftRun(item)));
    } else {
      setDriftRuns([]);
      messages.push("No se pudieron cargar las ejecuciones de drift.");
    }

    if (activeModelResult.status === "fulfilled") {
      setActiveModel(activeModelResult.value);
    } else {
      setActiveModel(null);
      messages.push("No se pudo cargar el modelo activo.");
    }

    if (fraudEvolutionResult.status === "fulfilled") {
      setFraudEvolutionData(normalizeFraudEvolution(fraudEvolutionResult.value));
      setFraudEvolutionError(false);
    } else {
      setFraudEvolutionData(buildMockFraudEvolution());
      setFraudEvolutionError(true);
      usedFallbackForAnalytics = true;
    }

    if (riskDistributionResult.status === "fulfilled") {
      setRiskDistributionData(normalizeRiskDistribution(riskDistributionResult.value));
      setRiskDistributionError(false);
    } else {
      setRiskDistributionData(buildMockRiskDistribution());
      setRiskDistributionError(true);
      usedFallbackForAnalytics = true;
    }

    if (classificationSummaryResult.status === "fulfilled") {
      setClassificationData(normalizeClassificationSummary(classificationSummaryResult.value));
      setClassificationError(false);
    } else {
      setClassificationData(buildMockClassificationSummary());
      setClassificationError(true);
      usedFallbackForAnalytics = true;
    }

    if (variableImportanceResult.status === "fulfilled") {
      setVariableImportanceData(normalizeVariableImportance(variableImportanceResult.value));
      setVariableImportanceError(false);
    } else {
      setVariableImportanceData(buildMockVariableImportance());
      setVariableImportanceError(true);
      usedFallbackForAnalytics = true;
    }

    if (usedFallbackForAnalytics) {
      messages.push("Mostrando datos de ejemplo porque no se pudieron cargar las métricas reales.");
    }

    setApiMessage(messages.join(" "));
    setLoading(false);
  }, []);

  useEffect(() => {
    loadAnalysisData();
  }, [loadAnalysisData]);

  const latestDrift = driftRuns[0] || null;

  return (
    <AppLayout>
      <PageHeader
        title="Análisis Visual"
        subtitle="Evolución, distribución e importancia de variables"
        badge="Últimos 30 días"
        actionLabel="Actualizar"
        onAction={loadAnalysisData}
      />

      {loading ? <p className="notice">Cargando datos analíticos...</p> : null}
      {apiMessage ? <p className="notice warn">{apiMessage}</p> : null}

      <Card style={{ marginBottom: 14 }}>
        <h3 className="section-title">Estado de drift y modelo</h3>
        {latestDrift ? (
          <div className="table-like">
            <article className="data-card">
              <div className="data-row"><strong>PSI último</strong><span>{latestDrift.psi ?? "N/A"}</span></div>
              <div className="data-row"><strong>Status</strong><span>{latestDrift.status}</span></div>
              <div className="data-row"><strong>sample_size</strong><span>{latestDrift.sample_size ?? "N/A"}</span></div>
              <div className="data-row"><strong>Fecha</strong><span>{latestDrift.created_at_label}</span></div>
              <div className="data-row"><strong>Modelo activo</strong><span>{activeModel?.name || "N/A"}</span></div>
              <div className="data-row"><strong>Versión</strong><span>{activeModel?.created_at ? formatDate(activeModel.created_at) : "N/A"}</span></div>
            </article>
          </div>
        ) : (
          <p className="notice">Aún no hay ejecuciones de drift registradas.</p>
        )}
      </Card>

      <section className="charts-grid">
        <FraudEvolutionChart data={fraudEvolutionData} loading={loading} error={fraudEvolutionError} />
        <RiskDonutChart data={riskDistributionData} loading={loading} error={riskDistributionError} />
        <FinalClassificationChart data={classificationData} loading={loading} error={classificationError} />
        <VariableImportanceChart
          data={variableImportanceData.items}
          source={variableImportanceData.source}
          loading={loading}
          error={variableImportanceError}
        />
      </section>
    </AppLayout>
  );
}
