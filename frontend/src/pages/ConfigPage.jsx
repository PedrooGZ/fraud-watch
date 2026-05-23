import { useCallback, useEffect, useMemo, useState } from "react";
import AppLayout from "../components/layout/AppLayout";
import PageHeader from "../components/layout/PageHeader";
import PolicySettingsPanel from "../components/fraud/PolicySettingsPanel";
import { useAuth } from "../context/AuthContext";
import { policyConfig } from "../data/mockData";
import { api } from "../services/api";
import { normalizePolicy, policyUiToPayload } from "../utils/adapters";

function getFallbackPolicy() {
  const rawPriority = (policyConfig.priority || "Riesgo").toLowerCase();
  const rawErrorCost = (policyConfig.errorCost || "FN > FP").toLowerCase();

  return {
    threshold_cost: Number(policyConfig.threshold ?? 0.82),
    max_alerts: Number(policyConfig.capacity ?? 50),
    priority_mode: rawPriority.includes("impact") ? "impact" : rawPriority.includes("mixto") ? "mixed" : "risk",
    error_cost_mode: rawErrorCost.includes("fp > fn")
      ? "reduce_fp"
      : rawErrorCost.includes("fn > fp")
        ? "reduce_fn"
        : "balanced",
    source: "mock_fallback",
  };
}

function validatePolicy(policy) {
  if (Number.isNaN(Number(policy.threshold_cost)) || Number(policy.threshold_cost) < 0 || Number(policy.threshold_cost) > 1) {
    return "El umbral debe estar entre 0 y 1.";
  }
  const maxAlerts = Number(policy.max_alerts);
  if (Number.isNaN(maxAlerts) || maxAlerts < 0 || !Number.isInteger(maxAlerts)) {
    return "La capacidad diaria debe ser mayor o igual que 0.";
  }
  if (!["risk", "impact", "mixed"].includes(policy.priority_mode)) {
    return "El modo de prioridad no es válido.";
  }
  if (!["balanced", "reduce_fp", "reduce_fn"].includes(policy.error_cost_mode)) {
    return "El modo de coste de errores no es válido.";
  }
  return "";
}

export default function ConfigPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const canEditPolicy = isAdmin;

  const fallbackPolicy = useMemo(() => getFallbackPolicy(), []);
  const [policy, setPolicy] = useState(fallbackPolicy);
  const [changeReason, setChangeReason] = useState("");
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyError, setHistoryError] = useState(false);
  const [saving, setSaving] = useState(false);
  const [usingFallback, setUsingFallback] = useState(false);
  const [saveMessage, setSaveMessage] = useState("");
  const [saveMessageType, setSaveMessageType] = useState("");

  const loadPolicy = useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.getPolicy();
      const normalized = normalizePolicy(response);
      setPolicy(normalized);
      setUsingFallback(false);
      return true;
    } catch {
      setPolicy(fallbackPolicy);
      setUsingFallback(true);
      return false;
    } finally {
      setLoading(false);
    }
  }, [fallbackPolicy]);

  const loadHistory = useCallback(async () => {
    setHistoryLoading(true);
    setHistoryError(false);
    try {
      const response = await api.getPolicyHistory({ limit: 20, offset: 0 });
      setHistory(Array.isArray(response) ? response : []);
    } catch {
      setHistory([]);
      setHistoryError(true);
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  useEffect(() => {
    async function bootstrap() {
      const policyLoaded = await loadPolicy();
      if (policyLoaded) {
        await loadHistory();
      } else {
        setHistory([]);
        setHistoryError(true);
        setHistoryLoading(false);
      }
    }
    bootstrap();
  }, [loadHistory, loadPolicy]);

  const handleSave = useCallback(async () => {
    if (!canEditPolicy) {
      setSaveMessage("No tienes permisos para modificar la política.");
      setSaveMessageType("error");
      return;
    }

    const validationError = validatePolicy(policy);
    if (validationError) {
      setSaveMessage(validationError);
      setSaveMessageType("error");
      return;
    }

    setSaveMessage("");
    setSaveMessageType("");
    setSaving(true);

    try {
      const payload = {
        ...policyUiToPayload(policy),
        reason: changeReason.trim() || "Actualización desde panel de configuración",
      };
      await api.updatePolicy(payload);
      setSaveMessage("Cambios guardados correctamente.");
      setSaveMessageType("success");
      setChangeReason("");
      await loadPolicy();
      await loadHistory();
    } catch (error) {
      if (error?.status === 403) {
        setSaveMessage("No tienes permisos para modificar la política.");
      } else {
        setSaveMessage("No se pudo guardar la política en la API.");
      }
      setSaveMessageType("error");
    } finally {
      setSaving(false);
    }
  }, [canEditPolicy, changeReason, loadHistory, loadPolicy, policy]);

  return (
    <AppLayout>
      <PageHeader
        title="Configuración"
        subtitle="Controla umbrales, priorización y política de errores."
        badge={usingFallback ? "Modo ejemplo" : "Política activa"}
        actionLabel={!canEditPolicy ? "Solo admin" : saving ? "Guardando..." : "Guardar cambios"}
        actionDisabled={saving || loading || !canEditPolicy}
        onAction={handleSave}
      />

      {loading ? <p className="notice">Cargando política...</p> : null}

      <PolicySettingsPanel
        value={policy}
        onChange={setPolicy}
        changeReason={changeReason}
        onChangeReason={setChangeReason}
        loading={loading}
        saving={saving}
        saveMessage={saveMessage}
        saveMessageType={saveMessageType}
        usingFallback={usingFallback}
        history={history}
        historyLoading={historyLoading}
        historyError={historyError}
        canEdit={canEditPolicy}
        currentUserRole={user?.role}
      />
    </AppLayout>
  );
}
