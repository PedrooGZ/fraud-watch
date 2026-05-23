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

export default function RegisterPage() {
  const navigate = useNavigate();
  const { registerUser } = useAuth();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [role, setRole] = useState("analyst");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (fullName.trim().length < 2) {
      setError("El nombre completo debe tener al menos 2 caracteres.");
      return;
    }
    if (!email.trim()) {
      setError("El email es obligatorio.");
      return;
    }
    if (password.length < 8) {
      setError("La contraseña debe tener al menos 8 caracteres.");
      return;
    }
    if (confirmPassword !== password) {
      setError("Las contraseñas no coinciden.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      await registerUser({
        email: email.trim(),
        full_name: fullName.trim(),
        password,
        role,
      });
      navigate("/dashboard", { replace: true });
    } catch (err) {
      const message = String(err?.message || "").toLowerCase();
      if (message.includes("email") && message.includes("registered")) {
        setError("Ese email ya está registrado.");
      } else {
        setError("No se pudo crear la cuenta.");
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
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 16 }}><Button onClick={() => navigate("/login")}>Iniciar Sesión</Button><Button>Registrarse</Button></div>
          <h2 style={{ marginTop: 0 }}>Registro</h2>
          {error ? <p className="notice error">{error}</p> : null}
          <form style={{ display: "grid", gap: 14 }} onSubmit={handleSubmit}>
            <TextInput label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} disabled={loading} required />
            <TextInput label="Contraseña" type="password" value={password} onChange={(e) => setPassword(e.target.value)} disabled={loading} required />
            <TextInput label="Confirmar contraseña" type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} disabled={loading} required />
            <TextInput label="Nombre completo" value={fullName} onChange={(e) => setFullName(e.target.value)} disabled={loading} required />
            <label className="input-wrap">
              <span>Rol</span>
              <select className="input" value={role} onChange={(e) => setRole(e.target.value)} disabled={loading}>
                <option value="analyst">Analista</option>
                <option value="admin">Admin</option>
              </select>
            </label>
            <Button variant="primary" block type="submit" disabled={loading}>{loading ? "Creando cuenta..." : "Continuar"}</Button>
          </form>
        </Card>
      </div>
    </main>
  );
}
