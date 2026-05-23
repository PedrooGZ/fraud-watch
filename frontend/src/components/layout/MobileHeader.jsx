import logo from "../../assets/logo-placeholder.svg";

export default function MobileHeader({ onMenu, apiStatusText, apiStatusVariant }) {
  return (
    <header className="mobile-header">
      <div className="brand" style={{ minWidth: 0 }}>
        <img src={logo} alt="FW" style={{ width: 34, height: 34 }} />
        <div style={{ minWidth: 0 }}>
          <h2 style={{ fontSize: "1rem" }}>Fraud Watch</h2>
          <p className={`api-status ${apiStatusVariant || "loading"}`.trim()} style={{ marginTop: 2 }}>{apiStatusText}</p>
        </div>
      </div>
      <button className="btn" type="button" onClick={onMenu} aria-label="Abrir menú">☰</button>
    </header>
  );
}
