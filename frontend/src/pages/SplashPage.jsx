import { useNavigate } from "react-router-dom";
import logo from "../assets/logo-placeholder.svg";
import Button from "../components/ui/Button";

export default function SplashPage() {
  const navigate = useNavigate();
  return (
    <main className="page-shell" style={{ display: "grid", placeItems: "center" }}>
      <section style={{ display: "grid", gap: 18, justifyItems: "center", textAlign: "center" }}>
        <img src={logo} alt="FW" style={{ width: "min(42vw, 180px)" }} />
        <h1 style={{ margin: 0, fontSize: "clamp(2rem, 8vw, 4.2rem)" }}>Fraud Watch</h1>
        <p style={{ margin: 0, color: "var(--text-soft)", fontSize: "clamp(1.1rem, 4vw, 2rem)" }}>Detección y revisión</p>
        <Button variant="primary" onClick={() => navigate("/login")}>Entrar</Button>
      </section>
    </main>
  );
}

