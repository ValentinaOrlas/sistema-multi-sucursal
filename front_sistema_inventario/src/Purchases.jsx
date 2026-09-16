import { useEffect, useState } from "react";
import { all, amount, date, purchaseTotal } from "./api";
import Icon from "./Icons";
import PurchaseForm from "./PurchaseForm";

export default function Purchases({ user, products, branches, catalogError }) {
  const admin = user.rol.nombre === "ADMIN_GENERAL";
  const [branchId, setBranchId] = useState(String(user.sucursal_id || ""));
  const [orders, setOrders] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [revision, setRevision] = useState(0);
  const [tab, setTab] = useState("orders");
  const [query, setQuery] = useState("");
  const [supplierId, setSupplierId] = useState("");
  const [productId, setProductId] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [modal, setModal] = useState(null);
  const [message, setMessage] = useState("");
  const branch = branches.find((b) => String(b.id) === branchId);
  const ready = branch?.activa && products.length > 0 && suppliers.length > 0;
  useEffect(() => {
    const controller = new AbortController();
    let inFlight = false;
    async function refresh() {
      if (inFlight) return;
      inFlight = true;
      try {
        const params = new URLSearchParams();
        if (branchId) params.set("sucursal_id", branchId);
        if (supplierId) params.set("proveedor_id", supplierId);
        if (productId) params.set("producto_id", productId);
        const [nextOrders, nextSuppliers] = await Promise.all([
          all(`/compras?${params}`, controller.signal),
          all("/proveedores", controller.signal),
        ]);
        if (!controller.signal.aborted) {
          setOrders(nextOrders);
          setSuppliers(nextSuppliers);
          setError("");
        }
      } catch (e) {
        if (!controller.signal.aborted)
          setError(
            e.message === "Failed to fetch"
              ? "No se pudo conectar con el servidor."
              : e.message,
          );
      } finally {
        inFlight = false;
        if (!controller.signal.aborted) setLoading(false);
      }
    }
    refresh();
    const interval = setInterval(() => {
      if (!document.hidden) refresh();
    }, 15000);
    const focus = () => {
      if (!document.hidden) refresh();
    };
    document.addEventListener("visibilitychange", focus);
    return () => {
      controller.abort();
      clearInterval(interval);
      document.removeEventListener("visibilitychange", focus);
    };
  }, [branchId, supplierId, productId, revision]);
  function changed(setter, value) {
    setLoading(true);
    setter(value);
    setPage(1);
  }
  const supplierMap = new Map(suppliers.map((s) => [s.id, s]));
  const visible =
    tab === "orders"
      ? orders.filter(
          (o) =>
            (!status || o.estado === status) &&
            `${o.id} ${supplierMap.get(o.proveedor_id)?.nombre || ""}`
              .toLowerCase()
              .includes(query.toLowerCase()),
        )
      : suppliers.filter((s) =>
          `${s.nombre} ${s.contacto || ""}`
            .toLowerCase()
            .includes(query.toLowerCase()),
        );
  const pages = Math.max(1, Math.ceil(visible.length / 10));
  const current = Math.min(page, pages);
  const rows = visible.slice((current - 1) * 10, current * 10);
  return (
    <main className="content">
      <div className="page-heading">
        <div>
          <span className="section-kicker">DEL PROVEEDOR A TU SUCURSAL</span>
          <h1>Compras</h1>
          <p>Planifica el abastecimiento y recibe tu tecnología con control.</p>
        </div>
        <div className="heading-actions">
          {admin && (
            <button
              className="secondary"
              onClick={() => setModal({ mode: "supplier" })}
            >
              <Icon name="plus" size={17} />
              Nuevo proveedor
            </button>
          )}
          <button
            className="primary"
            disabled={!ready}
            onClick={() => setModal({ mode: "create" })}
          >
            <Icon name="plus" size={18} />
            Nueva orden
          </button>
        </div>
      </div>
      <div className="scope-bar">
        <label className="branch-select">
          <Icon name="branch" />
          <span>Sucursal receptora</span>
          <select
            aria-label="Sucursal de compras"
            value={branchId}
            onChange={(e) => changed(setBranchId, e.target.value)}
          >
            {admin && <option value="">Todas las sucursales</option>}
            {branches
              .filter((b) => admin || b.id === user.sucursal_id)
              .map((b) => (
                <option key={b.id} value={b.id}>
                  {b.nombre}
                  {!b.activa ? " · Inactiva" : ""}
                </option>
              ))}
          </select>
        </label>
        <button
          className="text-button"
          disabled={loading}
          onClick={() => {
            setLoading(true);
            setRevision((x) => x + 1);
          }}
        >
          <Icon name="refresh" size={16} />
          {loading ? "Actualizando…" : "Actualizar"}
        </button>
      </div>
      {(error || catalogError) && (
        <div className="notice error" role="alert">
          {error || catalogError}
        </div>
      )}
      {message && (
        <div className="notice" role="status">
          <Icon name="check" size={18} />
          {message}
          <button onClick={() => setMessage("")} aria-label="Cerrar aviso">
            <Icon name="close" size={15} />
          </button>
        </div>
      )}
      {!ready && !loading && (
        <div className="notice">
          {!branch
            ? "Selecciona una sucursal para crear una orden."
            : !branch.activa
              ? "La sucursal está inactiva. Puedes consultar sus compras."
              : !suppliers.length
                ? "Registra un proveedor para comenzar. Esta acción corresponde al administrador."
                : "Registra primero los productos tecnológicos en el módulo de inventario."}
        </div>
      )}
      <section className="stats" aria-label="Resumen de compras filtradas">
        <article>
          <div className="stat-label">
            Órdenes consultadas
            <Icon name="grid" />
          </div>
          <strong>{orders.length}</strong>
          <small>Según sucursal, proveedor y producto</small>
        </article>
        <article className="warning-stat">
          <div className="stat-label">
            Por recibir
            <Icon name="box" />
          </div>
          <strong>
            {orders.filter((o) => o.estado === "PENDIENTE").length}
          </strong>
          <small>Pendientes de recepción</small>
        </article>
        <article>
          <div className="stat-label">
            Recibidas
            <Icon name="check" />
          </div>
          <strong>
            {orders.filter((o) => o.estado === "RECIBIDA").length}
          </strong>
          <small>Ingreso confirmado en inventario</small>
        </article>
        <article>
          <div className="stat-label">
            Canceladas
            <Icon name="close" />
          </div>
          <strong>
            {orders.filter((o) => o.estado === "CANCELADA").length}
          </strong>
          <small>Sin modificación de existencias</small>
        </article>
      </section>
      <section className="table-panel">
        <div
          className="purchase-tabs"
          role="group"
          aria-label="Secciones de compras"
        >
          <button
            className={tab === "orders" ? "selected" : ""}
            aria-pressed={tab === "orders"}
            onClick={() => {
              setTab("orders");
              setQuery("");
              setPage(1);
            }}
          >
            Órdenes de compra
          </button>
          <button
            className={tab === "suppliers" ? "selected" : ""}
            aria-pressed={tab === "suppliers"}
            onClick={() => {
              setTab("suppliers");
              setQuery("");
              setPage(1);
            }}
          >
            Proveedores
          </button>
        </div>
        <div className="table-heading">
          <div>
            <h2>
              {tab === "orders"
                ? "Historial de compras"
                : "Proveedores de tecnología"}
              <span className="count-pill">{visible.length}</span>
            </h2>
            <p>
              {tab === "orders"
                ? "Consulta los detalles y confirma la recepción de cada orden."
                : "Contactos, condiciones comerciales y tiempos de entrega registrados."}
            </p>
          </div>
        </div>
        <div className="filters purchase-filters">
          <div className="search">
            <Icon name="search" size={18} />
            <input
              aria-label="Buscar compras o proveedores"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setPage(1);
              }}
              placeholder={
                tab === "orders"
                  ? "Buscar orden o proveedor…"
                  : "Buscar proveedor o contacto…"
              }
            />
          </div>
          {tab === "orders" && (
            <>
              <select
                aria-label="Filtrar proveedor"
                value={supplierId}
                onChange={(e) => changed(setSupplierId, e.target.value)}
              >
                <option value="">Todos los proveedores</option>
                {suppliers.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.nombre}
                  </option>
                ))}
              </select>
              <select
                aria-label="Filtrar producto comprado"
                value={productId}
                onChange={(e) => changed(setProductId, e.target.value)}
              >
                <option value="">Todos los productos</option>
                {products.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.sku} · {p.nombre}
                  </option>
                ))}
              </select>
              <select
                aria-label="Estado de compra"
                value={status}
                onChange={(e) => {
                  setStatus(e.target.value);
                  setPage(1);
                }}
              >
                <option value="">Todos los estados</option>
                <option value="PENDIENTE">Pendiente</option>
                <option value="RECIBIDA">Recibida</option>
                <option value="CANCELADA">Cancelada</option>
              </select>
            </>
          )}
        </div>
        {loading ? (
          <div className="empty-state" role="status">
            Consultando compras…
          </div>
        ) : !rows.length ? (
          <div className="empty-state">
            <div className="empty-icon">
              <Icon name="box" size={30} />
            </div>
            <h3>
              {query || supplierId || productId || status
                ? "No hay coincidencias"
                : tab === "orders"
                  ? "Tu próxima compra comienza aquí"
                  : "Aún no hay proveedores"}
            </h3>
            <p>
              Las órdenes y proveedores registrados aparecerán en esta sección.
            </p>
          </div>
        ) : (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  {(tab === "orders"
                    ? [
                        "Orden / creación",
                        "Proveedor",
                        "Sucursal",
                        "Importe neto",
                        "Estado",
                        "Acciones",
                      ]
                    : [
                        "Proveedor",
                        "Contacto",
                        "Condiciones",
                        "Entrega promedio",
                        "Acciones",
                      ]
                  ).map((h) => (
                    <th key={h}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((row) =>
                  tab === "orders" ? (
                    <tr key={row.id}>
                      <td>
                        <strong>OC-{String(row.id).padStart(5, "0")}</strong>
                        <small>{date(row.fecha_creacion)}</small>
                      </td>
                      <td>
                        {supplierMap.get(row.proveedor_id)?.nombre ||
                          `Proveedor #${row.proveedor_id}`}
                      </td>
                      <td>
                        {branches.find((b) => b.id === row.sucursal_destino_id)
                          ?.nombre || `Sucursal #${row.sucursal_destino_id}`}
                      </td>
                      <td>{amount(purchaseTotal(row))}</td>
                      <td>
                        <span
                          className={`badge ${row.estado === "RECIBIDA" ? "ok" : row.estado === "CANCELADA" ? "empty" : "low"}`}
                        >
                          {row.estado === "PENDIENTE"
                            ? "Pendiente"
                            : row.estado === "RECIBIDA"
                              ? "Recibida"
                              : "Cancelada"}
                        </span>
                      </td>
                      <td>
                        <button
                          className="text-button"
                          onClick={() =>
                            setModal({
                              mode: "view",
                              orderId: row.id,
                              branchId: row.sucursal_destino_id,
                            })
                          }
                        >
                          Ver orden #{row.id}
                          <Icon name="arrow" size={15} />
                        </button>
                      </td>
                    </tr>
                  ) : (
                    <tr key={row.id}>
                      <td>
                        <strong>{row.nombre}</strong>
                      </td>
                      <td>{row.contacto || "—"}</td>
                      <td className="reason-cell">
                        {row.condiciones_comerciales ||
                          "Sin condiciones registradas"}
                      </td>
                      <td>{row.tiempo_entrega_promedio_dias} días</td>
                      <td>
                        {admin ? (
                          <button
                            className="text-button"
                            onClick={() =>
                              setModal({ mode: "supplier", supplier: row })
                            }
                          >
                            <Icon name="edit" size={15} />
                            Editar {row.nombre}
                          </button>
                        ) : (
                          "Consulta"
                        )}
                      </td>
                    </tr>
                  ),
                )}
              </tbody>
            </table>
          </div>
        )}
        <div className="pagination">
          <span>{visible.length} registros</span>
          <div>
            <button
              disabled={current === 1}
              onClick={() => setPage(current - 1)}
            >
              Anterior
            </button>
            <span>
              {current} / {pages}
            </span>
            <button
              disabled={current === pages}
              onClick={() => setPage(current + 1)}
            >
              Siguiente
            </button>
          </div>
        </div>
      </section>
      <div className="page-footer">
        <span>
          <Icon name="lock" size={13} /> La recepción registra fecha,
          responsable, motivo y cantidades.
        </span>
        <span>Actualización cada 15 segundos</span>
      </div>
      {modal && (
        <PurchaseForm
          {...modal}
          user={user}
          branch={
            modal.branchId
              ? branches.find((b) => b.id === modal.branchId)
              : branch
          }
          suppliers={suppliers}
          products={products}
          onClose={() => setModal(null)}
          onSaved={(text) => {
            setModal(null);
            setMessage(text);
            setLoading(true);
            setRevision((x) => x + 1);
          }}
        />
      )}
    </main>
  );
}
