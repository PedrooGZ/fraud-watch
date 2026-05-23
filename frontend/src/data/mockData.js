export const currentUser = {
  name: "Carlos Gómez",
  role: "Analista de riesgo",
  avatar: "FW",
};

export const dashboardStats = [
  { title: "Predicciones recientes", value: "128", badge: "Actividad reciente", footer: "Lotes procesados recientes: 50" },
  { title: "Alertas generadas", value: "23", badge: "En revisión", footer: "Casos marcados para revisión: 23" },
  { title: "Registros inválidos", value: "17", badge: "Revisar datos", footer: "Errores de validación en predicciones recientes" },
  { title: "Modelo activo", value: "OK", badge: "Sin drift", footer: "Último entrenamiento: hace 8 días" },
];

export const priorityCases = [
  { id: "#A-1029", client: "Cliente 3921", amount: "€ 2.480", risk: 0.91 },
  { id: "#A-1040", client: "Cliente 1044", amount: "€ 860", risk: 0.76 },
];

export const reportHistory = [
  { date: "09/02/2026 12:10", id: "REP-20260209-001", period: "30 días", format: "JSON", generatedBy: "Carlos Gómez" },
  { date: "07/02/2026 09:25", id: "REP-20260207-004", period: "7 días", format: "CSV", generatedBy: "Laura Pérez" },
];

export const chartData = {
  evolution: [10, 14, 12, 18, 15, 22, 26, 21, 24, 30],
  donut: [38, 45, 17],
  classification: { review: 72, noReview: 28 },
  importance: [
    { label: "V14", value: 0.38 },
    { label: "V10", value: 0.31 },
    { label: "V12", value: 0.25 },
    { label: "Amount", value: 0.19 },
    { label: "V17", value: 0.13 },
  ],
};

export const policyConfig = { threshold: 0.82, capacity: 50, priority: "Riesgo", errorCost: "FN > FP" };
