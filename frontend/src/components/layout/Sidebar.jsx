import { NavLink, useLocation } from "react-router-dom";
import logo from "../../assets/logo-placeholder.svg";
import { currentUser } from "../../data/mockData";
import Button from "../ui/Button";

const links = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/analysis", label: "Análisis Visual" },
  { to: "/reports", label: "Informes" },
  { to: "/config", label: "Configuración" },
];

const roleMap = {
  analyst: "Analista de riesgo",
  admin: "Administrador",
};

export default function Sidebar({ apiStatusText, apiStatusVariant, user, onLogout }) {
  const { pathname } = useLocation();

  const fullName = user?.full_name || currentUser.name || "Usuario";
  const roleLabel = roleMap[user?.role] || user?.role || currentUser.role || "Rol";
  const emailLabel = user?.email || null;
  const avatarText = String(fullName || "U").trim().charAt(0).toUpperCase() || "U";

  return (
    <aside style={{ display: "flex", flexDirection: "column", minHeight: "100%" }}>
      <div className="brand">
        <img src={logo} alt="FW" />
        <div>
          <h2>Fraud Watch</h2>
          <p>Detección y revisión</p>
          <p className={`api-status ${apiStatusVariant || "loading"}`.trim()}>{apiStatusText}</p>
        </div>
      </div>
      <nav className="sidebar-nav">
        {links.map((link) => (
          <NavLink key={link.to} to={link.to} className={`sidebar-link ${pathname === link.to ? "active" : ""}`.trim()}>{link.label}</NavLink>
        ))}
      </nav>
      <div style={{ marginTop: "auto" }}>
        <div className="brand" style={{ marginBottom: 10 }}>
          <div style={{ width: 54, height: 54, borderRadius: 10, background: "#040e21", display: "grid", placeItems: "center", fontWeight: 700 }}>{avatarText}</div>
          <div>
            <h2 style={{ fontSize: "2rem" }}>{fullName}</h2>
            <p>{roleLabel}</p>
            {emailLabel ? <p className="api-status" style={{ marginTop: 2 }}>{emailLabel}</p> : null}
          </div>
        </div>
        <Button block onClick={onLogout}>Cerrar sesión</Button>
      </div>
    </aside>
  );
}
