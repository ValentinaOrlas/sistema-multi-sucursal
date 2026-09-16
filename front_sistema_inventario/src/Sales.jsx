import { useEffect, useState } from "react";
import { all, api, amount, date } from "./api";
import Icon from "./Icons";
import SaleForm from "./SaleForm";

export default function Sales({ user, products, branches, catalogError }) {
  const admin = user.rol.nombre === "ADMIN_GENERAL";
  const [branchId, setBranchId] = useState(String(user.sucursal_id || ""));
  const [sales, setSales] = useState([]);
  const [stocks, setStocks] = useState([]);
  const [priceLists, setPriceLists] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [revision, setRevision] = useState(0);
  const [query, setQuery] = useState("");
  const [productId, setProductId] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [page, setPage] = useState(1);
  const [modal, setModal] = useState(null);
  const [message, setMessage] = useState("");
  const branch = branches.find((b) => String(b.id) === branchId);
  useEffect(() => {
    const controller = new AbortController();
    let inFlight = false;
    async function refresh() {
      if (inFlight) return;
      inFlight = true;
      try {
        const query = branchId ? `?sucursal_id=${branchId}` : "";
        const [nextSales, nextStocks, lists] = await Promise.all([
          all(`/ventas${query}`, controller.signal),
          all(`/inventario${query}`, controller.signal),
          api("/listas-precios", { signal: controller.signal }),
        ]);
        if (!controller.signal.aborted) {
          setSales(nextSales);
          setStocks(nextStocks);
          setPriceLists(lists);
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
  }, [branchId, revision]);
  const names = new Map(products.map((p) => [p.id, p]));
  const invalidDates = from && to && from > to;
  const filtered = sales.filter((sale) => {
    const timestamp = new Date(
      /Z$|[+-]\d\d:\d\d$/.test(sale.fecha_venta)
        ? sale.fecha_venta
        : `${sale.fecha_venta}Z`,
    );
    const day = `${timestamp.getFullYear()}-${String(timestamp.getMonth() + 1).padStart(2, "0")}-${String(timestamp.getDate()).padStart(2, "0")}`;
    const text = `${sale.id} V-${String(sale.id).padStart(5, "0")} ${sale.detalles.map((d) => `${names.get(d.producto_id)?.nombre || ""} ${names.get(d.producto_id)?.sku || ""}`).join(" ")}`;
    return (
      !invalidDates &&
      (!from || day >= from) &&
      (!to || day <= to) &&
      (!productId ||
        sale.detalles.some((d) => String(d.producto_id) === productId)) &&
      text.toLowerCase().includes(query.toLowerCase())
    );
  });
  const pages = Math.max(1, Math.ceil(filtered.length / 10));
  const current = Math.min(page, pages);
  const total = filtered.reduce(
    (sum, sale) => sum + Number(sale.total_venta),
    0,
  );
  return (
    <main className="content">
      <div className="page-heading">
        <div>
          <span className="section-kicker">CADA VENTA, BAJO CONTROL</span>
          <h1>Ventas</h1>
          <p>Registra salidas comerciales y consulta sus comprobantes.</p>
        </div>
        <button
          className="primary"
          disabled={
            !branch?.activa ||
            !products.length ||
            loading ||
            Boolean(error || catalogError)
          }
          onClick={() => setModal({})}
        >
          <Icon name="plus" size={18} />
          Nueva venta
        </button>
      </div>
      <div className="scope-bar">
        <label className="branch-select">
          <Icon name="branch" />
          <span>Sucursal de venta</span>
          <select
            aria-label="Sucursal de ventas"
            value={branchId}
            onChange={(e) => {
              setBranchId(e.target.value);
              setLoading(true);
              setPage(1);
            }}
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
          <button aria-label="Cerrar aviso" onClick={() => setMessage("")}>
            <Icon name="close" size={15} />
          </button>
        </div>
      )}
      {!branch && !loading && (
        <div className="notice">
          Selecciona una sucursal para registrar una venta.
        </div>
      )}
      {branch && !branch.activa && (
        <div className="notice">
          Sucursal inactiva. Solo se permite consultar su historial.
        </div>
      )}
      <section className="stats" aria-label="Resumen de ventas filtradas">
        <article>
          <div className="stat-label">
            Ventas registradas
            <Icon name="grid" />
          </div>
          <strong>{filtered.length}</strong>
          <small>Según los filtros seleccionados</small>
        </article>
        <article>
          <div className="stat-label">
            Importe vendido
            <Icon name="check" />
          </div>
          <strong className="stat-money">{amount(total)}</strong>
          <small>Totales confirmados por el servidor</small>
        </article>
        <article>
          <div className="stat-label">
            Promedio por venta
            <Icon name="box" />
          </div>
          <strong className="stat-money">
            {amount(filtered.length ? total / filtered.length : 0)}
          </strong>
          <small>Descuentos incluidos</small>
        </article>
        <article>
          <div className="stat-label">
            Productos vendidos
            <Icon name="laptop" />
          </div>
          <strong>
            {
              new Set(
                filtered.flatMap((s) => s.detalles.map((d) => d.producto_id)),
              ).size
            }
          </strong>
          <small>Referencias distintas</small>
        </article>
      </section>
      <section className="table-panel">
        <div className="table-heading">
          <div>
            <h2>
              Historial de ventas
              <span className="count-pill">{filtered.length}</span>
            </h2>
            <p>
              Consulta el detalle, la fecha y el responsable de cada
              transacción.
            </p>
          </div>
        </div>
        <div className="filters sales-filters">
          <div className="search">
            <Icon name="search" size={18} />
            <input
              aria-label="Buscar ventas"
              placeholder="Buscar comprobante, producto o SKU…"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setPage(1);
              }}
            />
          </div>
          <select
            aria-label="Filtrar producto vendido"
            value={productId}
            onChange={(e) => {
              setProductId(e.target.value);
              setPage(1);
            }}
          >
            <option value="">Todos los productos</option>
            {products.map((p) => (
              <option key={p.id} value={p.id}>
                {p.sku} · {p.nombre}
              </option>
            ))}
          </select>
          <label>
            Desde
            <input
              type="date"
              value={from}
              max={to || undefined}
              onChange={(e) => {
                setFrom(e.target.value);
                setPage(1);
              }}
            />
          </label>
          <label>
            Hasta
            <input
              type="date"
              value={to}
              min={from || undefined}
              onChange={(e) => {
                setTo(e.target.value);
                setPage(1);
              }}
            />
          </label>
        </div>
        {invalidDates && (
          <div className="notice error" role="alert">
            La fecha inicial debe ser anterior o igual a la final.
          </div>
        )}
        {loading ? (
          <div className="empty-state" role="status">
            Consultando ventas…
          </div>
        ) : !filtered.length ? (
          <div className="empty-state">
            <div className="empty-icon">
              <Icon name="box" size={30} />
            </div>
            <h3>
              {query || productId || from || to
                ? "No hay ventas con estos filtros"
                : "Tu primera venta comienza aquí"}
            </h3>
            <p>
              Registra una venta para consultar su comprobante y conservar su
              trazabilidad.
            </p>
          </div>
        ) : (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Comprobante / fecha</th>
                  <th>Sucursal</th>
                  <th>Responsable</th>
                  <th>Productos</th>
                  <th>Total confirmado</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                {filtered
                  .slice((current - 1) * 10, current * 10)
                  .map((sale) => (
                    <tr key={sale.id}>
                      <td>
                        <strong>V-{String(sale.id).padStart(5, "0")}</strong>
                        <small>{date(sale.fecha_venta)}</small>
                      </td>
                      <td>
                        {branches.find((b) => b.id === sale.sucursal_id)
                          ?.nombre || `Sucursal #${sale.sucursal_id}`}
                      </td>
                      <td>
                        {sale.usuario_id === user.id
                          ? user.nombre
                          : `Usuario #${sale.usuario_id}`}
                      </td>
                      <td>{sale.detalles.length}</td>
                      <td>
                        <strong>{amount(sale.total_venta)}</strong>
                      </td>
                      <td>
                        <button
                          className="text-button"
                          onClick={() => setModal({ saleId: sale.id })}
                        >
                          Ver venta #{sale.id}
                          <Icon name="arrow" size={15} />
                        </button>
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        )}
        <div className="pagination">
          <span>{filtered.length} registros</span>
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
          <Icon name="lock" size={13} />
          Stock validado antes de confirmar cada venta.
        </span>
        <span>Actualización cada 15 segundos</span>
      </div>
      {modal && (
        <SaleForm
          key={modal.saleId || "new"}
          {...modal}
          user={user}
          branch={branch}
          branches={branches}
          products={products}
          stocks={stocks}
          priceLists={priceLists}
          onClose={() => setModal(null)}
          onSaved={(sale) => {
            setModal({ saleId: sale.id });
            setMessage(
              `Venta #${sale.id} registrada por ${amount(sale.total_venta)}. Inventario actualizado.`,
            );
            setLoading(true);
            setRevision((x) => x + 1);
          }}
        />
      )}
    </main>
  );
}
