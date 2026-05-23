import { useState } from "react";
import { useNavigate } from "react-router-dom";
import logo from "../assets/logo-placeholder.svg";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import TextInput from "../components/ui/TextInput";
import { useAuth } from "../context/AuthContext";

const features = [
  { title: "Explicabilidad", text: "Motivos de riesgo por transacción." },
  { title: "Control", text: "Umbral, capacidad diaria y coste FP/FN." },
  { title: "Visual", text: "Gráficas claras sin tablas interminables." },
  { title: "Trazabilidad", text: "Cambios y decisiones registrados." },
];

export default function LoginPage() {
  const navigate = useNavigate();
  const { loginUser } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!email.trim() || !password) {
      setError("Completa email y contraseña.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      await loginUser({ email: email.trim(), password });
      navigate("/dashboard", { replace: true });
    } catch (err) {
      if (err?.status === 401) {
        setError("Credenciales incorrectas.");
      } else {
        setError("No se pudo iniciar sesión.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="page-shell" style={{ display: "grid", alignItems: "center" }}>
      <div className="auth-grid">
        <Card className="panel">
          <div className="brand" style={{ marginBottom: 16 }}><img src={logo} alt="FW" /><div><h1 style={{ margin: 0 }}>Fraud Watch</h1><p>Detección y revisión</p></div></div>
          <p style={{ color: "var(--text-soft)" }}>Panel profesional con explicaciones claras: evolución del fraude, distribución del riesgo y factores que influyen en cada decisión del modelo.</p>
          <div className="feature-grid" style={{ marginTop: 18 }}>{features.map((f) => <article className="feature-box" key={f.title}><h3 style={{ marginTop: 0 }}>{f.title}</h3><p style={{ marginBottom: 0 }}>{f.text}</p></article>)}</div>
        </Card>
        <Card className="panel">
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 16 }}><Button>Iniciar Sesión</Button><Button onClick={() => navigate("/register")}>Registrarse</Button></div>
          <h2 style={{ marginTop: 0 }}>Acceso</h2>
          {error ? <p className="notice error">{error}</p> : null}
          <form style={{ display: "grid", gap: 14 }} onSubmit={handleSubmit}>
            <TextInput label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} disabled={loading} required />
            <TextInput label="Contraseña" type="password" value={password} onChange={(e) => setPassword(e.target.value)} disabled={loading} required />
            <Button variant="primary" block type="submit" disabled={loading}>{loading ? "Iniciando..." : "Continuar"}</Button>
          </form>
        </Card>
      </div>
    </main>
  );
}
