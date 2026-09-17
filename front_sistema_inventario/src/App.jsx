import { useEffect, useState } from "react";
import { api, session } from "./api";
import Icon from "./Icons";
import Inventory from "./Inventory";
import "./App.css";

export default function App() {
  const [user, setUser] = useState(session.user);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    const expired = () => {
      setUser(null);
      setError("Tu sesión terminó. Inicia sesión de nuevo.");
    };
    window.addEventListener("session-expired", expired);
    return () => {
      window.removeEventListener("session-expired", expired);
    };
  }, []);
  async function login(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const data = Object.fromEntries(new FormData(event.currentTarget));
    try {
      const result = await api("/auth/login", { method: "POST", body: data });
      const currentUser = {
        ...result.usuario,
        rol: { nombre: result.usuario.rol },
      };
      session.set(result.access_token, currentUser);
      setUser(currentUser);
    } catch (e) {
      session.clear();
      setError(
        e.message === "Failed to fetch"
          ? "No se pudo conectar con el servidor. Intenta nuevamente."
          : e.message,
      );
    } finally {
      setBusy(false);
    }
  }
  if (user)
    return (
      <Inventory
        user={user}
        onLogout={() => {
          session.clear();
          setUser(null);
          setError("");
        }}
      />
    );
  return (
    <main className="login-layout">
      <section className="login-story">
        <div className="brand">
          <span className="brand-mark">
            <Icon />
          </span>
          nodo<span className="brand-dot">.</span>
        </div>
        <div>
          <span className="eyebrow">INVENTARIO MULTISUCURSAL</span>
          <h1>
            Toda tu tecnología.
            <br />
            En el lugar correcto.
          </h1>
          <p>
            Conecta tus sucursales y mantén el control de cada producto, cada
            unidad y cada movimiento.
          </p>
          <div className="network-art" aria-hidden="true">
            <div>
              <Icon name="branch" size={30} />
              <span>Una red conectada</span>
            </div>
            <span className="network-line" />
            <div>
              <Icon name="box" size={30} />
              <span>Inventario visible</span>
            </div>
            <span className="network-line" />
            <div>
              <Icon name="check" size={30} />
              <span>Control en cada paso</span>
            </div>
          </div>
        </div>
        <small>Gestión de artículos tecnológicos · nodo</small>
      </section>
      <section className="login-panel">
        <div className="login-card">
          <span className="section-kicker">BIENVENIDO DE NUEVO</span>
          <h2>Ingresa a tu espacio</h2>
          <p>Usa las credenciales asignadas por tu administrador.</p>
          <form onSubmit={login}>
            <label>
              Correo electrónico
              <input
                name="email"
                type="email"
                placeholder="tu@empresa.com"
                autoComplete="username"
                required
                autoFocus
              />
            </label>
            <label>
              Contraseña
              <input
                name="password"
                type="password"
                placeholder="Tu contraseña"
                autoComplete="current-password"
                required
              />
            </label>
            {error && (
              <div role="alert" className="notice error">
                {error}
              </div>
            )}
            <button className="primary" disabled={busy}>
              {busy ? "Ingresando…" : "Iniciar sesión"}
              <Icon name="arrow" />
            </button>
          </form>
          <div className="login-foot">
            <Icon name="lock" size={15} /> Acceso según tu rol y sucursal
            asignada
          </div>
        </div>
      </section>
    </main>
  );
}
