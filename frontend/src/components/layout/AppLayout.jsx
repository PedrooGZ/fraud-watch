import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import useHealth from "../../hooks/useHealth";
import MobileHeader from "./MobileHeader";
import Sidebar from "./Sidebar";

const mobileLinks = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/analysis", label: "Análisis Visual" },
  { to: "/reports", label: "Informes" },
  { to: "/config", label: "Configuración" },
];

export default function AppLayout({ children }) {
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();
  const { loading, online } = useHealth();
  const { user, logout } = useAuth();

  const apiConnected = online;
  const apiStatusText = loading
    ? "Comprobando API..."
    : apiConnected
      ? "API conectada"
      : "API no disponible · usando datos de ejemplo";
  const apiStatusVariant = loading ? "loading" : apiConnected ? "ok" : "down";

  const handleLogout = () => {
    logout();
    setOpen(false);
    navigate("/login", { replace: true });
  };

  return (
    <div className="app-layout">
      <MobileHeader onMenu={() => setOpen(true)} apiStatusText={apiStatusText} apiStatusVariant={apiStatusVariant} />
      {open ? (
        <div className="mobile-drawer" onClick={() => setOpen(false)}>
          <div className="mobile-drawer-panel" onClick={(e) => e.stopPropagation()}>
            <nav className="sidebar-nav" style={{ marginTop: 6 }}>
              {mobileLinks.map((link) => (
                <button key={link.to} type="button" className="sidebar-link" onClick={() => { navigate(link.to); setOpen(false); }}>{link.label}</button>
              ))}
              <button className="sidebar-link" type="button" onClick={handleLogout}>Cerrar sesión</button>
            </nav>
          </div>
        </div>
      ) : null}
      <aside className="desktop-sidebar panel">
        <Sidebar
          apiStatusText={apiStatusText}
          apiStatusVariant={apiStatusVariant}
          user={user}
          onLogout={handleLogout}
        />
      </aside>
      <main className="main-content">{children}</main>
    </div>
  );
}
