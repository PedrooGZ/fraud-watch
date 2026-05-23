import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import SplashPage from "./pages/SplashPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import DashboardPage from "./pages/DashboardPage";
import VisualAnalysisPage from "./pages/VisualAnalysisPage";
import ReportsPage from "./pages/ReportsPage";
import ConfigPage from "./pages/ConfigPage";

function ProtectedRoute({ children }) {
  const { loading, isAuthenticated } = useAuth();

  if (loading) {
    return <main className="page-shell"><p className="notice">Cargando sesión...</p></main>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

function PublicAuthRoute({ children }) {
  const { loading, isAuthenticated } = useAuth();

  if (loading) {
    return <main className="page-shell"><p className="notice">Cargando sesión...</p></main>;
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<SplashPage />} />
      <Route path="/login" element={<PublicAuthRoute><LoginPage /></PublicAuthRoute>} />
      <Route path="/register" element={<PublicAuthRoute><RegisterPage /></PublicAuthRoute>} />
      <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
      <Route path="/analysis" element={<ProtectedRoute><VisualAnalysisPage /></ProtectedRoute>} />
      <Route path="/reports" element={<ProtectedRoute><ReportsPage /></ProtectedRoute>} />
      <Route path="/config" element={<ProtectedRoute><ConfigPage /></ProtectedRoute>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
