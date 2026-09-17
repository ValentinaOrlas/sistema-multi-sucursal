const base = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(
  /\/$/,
  "",
);
export const session = {
  get: () => sessionStorage.getItem("inventario.token"),
  set: (token, user) => {
    sessionStorage.setItem("inventario.token", token);
    sessionStorage.setItem("inventario.user", JSON.stringify(user));
  },
  user: () => {
    try {
      const token = sessionStorage.getItem("inventario.token");
      if (!token) return null;
      const payload = JSON.parse(atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")));
      if (payload.exp * 1000 <= Date.now()) return null;
      return JSON.parse(sessionStorage.getItem("inventario.user"));
    } catch { return null; }
  },
  clear: () => {
    sessionStorage.removeItem("inventario.token");
    sessionStorage.removeItem("inventario.user");
  },
};
export async function api(path, { method = "GET", body, signal } = {}) {
  const token = session.get();
  const response = await fetch(`${base}/api${path}`, {
    method,
    signal,
    headers: {
      ...(body ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (response.status === 204) return null;
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (
      response.status === 401 &&
      path !== "/auth/login" &&
      token === session.get()
    ) {
      session.clear();
      window.dispatchEvent(new Event("session-expired"));
    }
    const detail = data.detail || data.error || data.mensaje;
    const message = Array.isArray(detail)
      ? detail
          .map((x) => `${x.loc?.slice(1).join(".") || "Datos"}: ${x.msg}`)
          .join(" · ")
      : detail;
    throw new Error(
      typeof message === "string"
        ? message
        : `No se pudo completar la operación (${response.status}).`,
    );
  }
  if (path.split("?")[0] === "/inventario/productos" && method === "GET") {
    const fields = ["id", "sku", "nombre", "descripcion", "categoria_id", "categoria", "unidad_medida", "stock_minimo_global"];
    return data.map(row => Array.isArray(row) ? Object.fromEntries(fields.map((field, i) => [field, row[i]])) : row);
  }
  if (path.split("?")[0] === "/inventario/movimientos" && method === "GET") {
    const fields = ["id", "sucursal_id", "sucursal", "producto_id", "sku", "producto", "cantidad", "tipo_movimiento", "motivo", "stock_resultante", "fecha_movimiento"];
    return data.map(row => Array.isArray(row) ? Object.fromEntries(fields.map((field, i) => [field, row[i]])) : row);
  }
  return data;
}
// El nuevo backend devuelve listas completas; no acepta paginación offset/limit.
export async function all(path, signal) {
  const data = await api(path, { signal });
  const rows = Array.isArray(data) ? data : data.proveedores;
  if (!Array.isArray(rows)) throw new Error("El servidor no devolvió una lista válida.");
  return rows;
}
export const number = (value) =>
  new Intl.NumberFormat("es-CO", { maximumFractionDigits: 3 }).format(
    Number(value || 0),
  );
export const amount = (value) =>
  new Intl.NumberFormat("es-CO", { maximumFractionDigits: 2 }).format(
    Number(value || 0),
  );
export function date(value) {
  if (!value) return "—";
  const utc = /Z$|[+-]\d\d:\d\d$/.test(value) ? value : `${value}Z`;
  return new Intl.DateTimeFormat("es-CO", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(utc));
}

export const purchaseTotal = (order) =>
  order.detalles.reduce(
    (sum, item) =>
      sum +
      Number(item.cantidad) *
        Number(item.precio_unitario) *
        (1 - Number(item.descuento) / 100),
    0,
  );
