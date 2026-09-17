import { useEffect, useRef, useState } from "react";
import { api, amount, date, number } from "./api";
import Icon from "./Icons";

const newLine = () => ({
  key: crypto.randomUUID(),
  producto_id: "",
  cantidad: "1",
  precio_unitario: "",
  descuento_aplicado: "0",
});
export default function SaleForm({
  saleId,
  user,
  branch,
  branches,
  products,
  stocks,
  priceLists,
  onClose,
  onSaved,
}) {
  const dialog = useRef(null);
  const sending = useRef(false);
  const [lines, setLines] = useState([newLine()]);
  const [listId, setListId] = useState("");
  const [prices, setPrices] = useState([]);
  const [priceLoading, setPriceLoading] = useState(false);
  const [sale, setSale] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [uncertain, setUncertain] = useState(false);
  const [priceError, setPriceError] = useState("");
  useEffect(() => {
    const element = dialog.current;
    const previous = document.activeElement;
    element.showModal();
    const controller = new AbortController();
    if (saleId)
      api(`/ventas/${saleId}`, { signal: controller.signal })
        .then(sale => setSale({ ...sale, id: sale.venta_id }))
        .catch((e) => {
          if (!controller.signal.aborted) setError(e.message);
        });
    return () => {
      controller.abort();
      element.close();
      previous?.focus();
    };
  }, [saleId]);
  useEffect(() => {
    if (!listId) return;
    const controller = new AbortController();
    api(`/listas-precios/${listId}/precios`, { signal: controller.signal })
      .then((rows) => {
        if (!controller.signal.aborted) setPrices(rows);
      })
      .catch((e) => {
        if (!controller.signal.aborted) setPriceError(e.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setPriceLoading(false);
      });
    return () => controller.abort();
  }, [listId]);
  const names = new Map(products.map((p) => [p.id, p]));
  const stockMap = new Map(
    stocks
      .filter((s) => s.sucursal_id === branch?.id)
      .map((s) => [s.producto_id, s]),
  );
  const priceMap = new Map(prices.map((p) => [p.producto_id, p.precio]));
  const priceFor = (line) =>
    listId ? priceMap.get(Number(line.producto_id)) : line.precio_unitario;
  const insufficient = lines.some(
    (line) =>
      line.producto_id &&
      Number(line.cantidad) >
        Number(stockMap.get(Number(line.producto_id))?.stock_actual || 0),
  );
  const missingPrice =
    Boolean(listId) &&
    lines.some(
      (line) => line.producto_id && !priceMap.has(Number(line.producto_id)),
    );
  const duplicate =
    new Set(lines.map((x) => x.producto_id).filter(Boolean)).size !==
    lines.filter((x) => x.producto_id).length;
  const estimate = lines.reduce(
    (sum, line) =>
      sum +
      Math.round(
        (Number(line.cantidad) *
          Number(priceFor(line) || 0) *
          (1 - Number(line.descuento_aplicado) / 100) +
          Number.EPSILON) *
          100,
      ) /
        100,
    0,
  );
  function update(key, field, value) {
    setLines((old) =>
      old.map((line) =>
        line.key === key ? { ...line, [field]: value } : line,
      ),
    );
  }
  async function submit(event) {
    event.preventDefault();
    if (
      saleId ||
      sending.current ||
      insufficient ||
      missingPrice ||
      duplicate ||
      uncertain ||
      priceError
    )
      return;
    sending.current = true;
    setBusy(true);
    setError("");
    try {
      const body = {
        sucursal_id: branch.id,
        usuario_id: user.id,
        detalles: lines.map((line) => ({
          producto_id: Number(line.producto_id),
          cantidad: line.cantidad,
          descuento_aplicado: line.descuento_aplicado,
          ...(!listId ? { precio_unitario: line.precio_unitario } : {}),
        })),
      };
      if (listId) body.lista_precio_id = Number(listId);
      const result = await api("/ventas", { method: "POST", body });
      const sale = result.comprobante;
      onSaved({ ...sale, id: sale.venta_id });
    } catch (e) {
      if (e instanceof TypeError) {
        setUncertain(true);
        setError(
          "La conexión se interrumpió. Consulta el historial antes de registrar otra venta: esta operación podría haberse guardado.",
        );
      } else setError(e.message);
    } finally {
      sending.current = false;
      setBusy(false);
    }
  }
  return (
    <dialog
      ref={dialog}
      className="modal purchase-modal"
      aria-labelledby="sale-title"
      onCancel={(e) => {
        e.preventDefault();
        if (!busy) onClose();
      }}
    >
      <header>
        <div>
          <span className="section-kicker">SALIDAS COMERCIALES</span>
          <h2 id="sale-title">
            {saleId ? `Comprobante de venta #${saleId}` : "Nueva venta"}
          </h2>
        </div>
        <button
          className="icon-button"
          type="button"
          aria-label="Cerrar ventana"
          disabled={busy}
          onClick={onClose}
        >
          <Icon name="close" />
        </button>
      </header>
      <form onSubmit={submit}>
        <div className="modal-body">
          {saleId ? (
            sale ? (
              <>
                <div className="notice">
                  <Icon name="check" size={18} />
                  Venta registrada. El retiro de inventario quedó confirmado.
                </div>
                <dl className="detail-grid">
                  <div>
                    <dt>Sucursal</dt>
                    <dd>
                      {branches.find((b) => b.id === sale.sucursal_id)
                        ?.nombre || `Sucursal #${sale.sucursal_id}`}
                    </dd>
                  </div>
                  <div>
                    <dt>Fecha de venta</dt>
                    <dd>{date(sale.fecha_venta)}</dd>
                  </div>
                  <div>
                    <dt>Responsable</dt>
                    <dd>
                      {sale.usuario_id === user.id
                        ? user.nombre
                        : `Usuario #${sale.usuario_id}`}
                    </dd>
                  </div>
                  <div>
                    <dt>Referencia</dt>
                    <dd>V-{String(sale.id).padStart(5, "0")}</dd>
                  </div>
                </dl>
                <div className="table-scroll">
                  <table>
                    <thead>
                      <tr>
                        <th>Producto</th>
                        <th>Cantidad</th>
                        <th>Precio unitario</th>
                        <th>Descuento</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sale.detalles.map((d) => (
                        <tr key={d.id}>
                          <td>
                            <strong>
                              {names.get(d.producto_id)?.nombre ||
                                `Producto #${d.producto_id}`}
                            </strong>
                            <small>{names.get(d.producto_id)?.sku}</small>
                          </td>
                          <td>
                            {number(d.cantidad)}
                            <small>
                              {names.get(d.producto_id)?.unidad_medida}
                            </small>
                          </td>
                          <td>{amount(d.precio_unitario)}</td>
                          <td>{number(d.descuento_aplicado)} %</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="purchase-total">
                  <span>Total confirmado</span>
                  <strong>{amount(sale.total_venta)}</strong>
                </div>
                <small>
                  Registro interno de venta. No es una factura fiscal.
                </small>
              </>
            ) : (
              <p role="status">
                {error
                  ? "No se pudo consultar el comprobante."
                  : "Consultando venta…"}
              </p>
            )
          ) : (
            <>
              <div className="notice">
                <Icon name="branch" size={18} />
                <span>
                  Sucursal: <strong>{branch.nombre}</strong> · Responsable:{" "}
                  <strong>{user.nombre}</strong>
                </span>
              </div>
              <label>
                Origen de precios
                <select
                  value={listId}
                  onChange={(e) => {
                    setListId(e.target.value);
                    setPrices([]);
                    setPriceError("");
                    setPriceLoading(Boolean(e.target.value));
                  }}
                >
                  <option value="">Precio manual por producto</option>
                  {priceLists.map((list) => (
                    <option key={list.id} value={list.id}>
                      {list.nombre}
                    </option>
                  ))}
                </select>
              </label>
              {lines.map((line, index) => {
                const product = names.get(Number(line.producto_id));
                const available =
                  stockMap.get(Number(line.producto_id))?.stock_actual || 0;
                return (
                  <fieldset className="purchase-line" key={line.key}>
                    <legend>Producto {index + 1}</legend>
                    <label>
                      Producto tecnológico
                      <select
                        required
                        value={line.producto_id}
                        onChange={(e) =>
                          update(line.key, "producto_id", e.target.value)
                        }
                      >
                        <option value="" disabled>
                          Selecciona un producto
                        </option>
                        {products.map((p) => (
                          <option key={p.id} value={p.id}>
                            {p.sku} · {p.nombre}
                          </option>
                        ))}
                      </select>
                    </label>
                    {product && (
                      <small
                        className={
                          Number(line.cantidad) > Number(available)
                            ? "stock-warning"
                            : ""
                        }
                      >
                        Disponible: {number(available)} {product.unidad_medida}.
                        Cantidad y precio en unidad base.
                      </small>
                    )}
                    <div className="purchase-line-values">
                      <label>
                        Cantidad
                        <input
                          type="number"
                          required
                          min="0.001"
                          max="99999999999.999"
                          step="0.001"
                          value={line.cantidad}
                          onChange={(e) =>
                            update(line.key, "cantidad", e.target.value)
                          }
                        />
                      </label>
                      <label>
                        Precio unitario
                        <input
                          type="number"
                          required
                          min="0"
                          max="9999999999.99"
                          step="0.01"
                          readOnly={Boolean(listId)}
                          value={priceFor(line) ?? ""}
                          onChange={(e) =>
                            update(line.key, "precio_unitario", e.target.value)
                          }
                        />
                      </label>
                      <label>
                        Descuento (%)
                        <input
                          type="number"
                          required
                          min="0"
                          max="100"
                          step="0.01"
                          value={line.descuento_aplicado}
                          onChange={(e) =>
                            update(
                              line.key,
                              "descuento_aplicado",
                              e.target.value,
                            )
                          }
                        />
                      </label>
                      <button
                        type="button"
                        className="icon-button"
                        aria-label={`Quitar producto ${index + 1}`}
                        disabled={lines.length === 1}
                        onClick={() =>
                          setLines((old) =>
                            old.filter((x) => x.key !== line.key),
                          )
                        }
                      >
                        <Icon name="trash" size={18} />
                      </button>
                    </div>
                  </fieldset>
                );
              })}
              <button
                className="secondary"
                type="button"
                disabled={lines.length >= 100}
                onClick={() => setLines((old) => [...old, newLine()])}
              >
                <Icon name="plus" size={16} />
                Agregar producto
              </button>
              {insufficient && (
                <div className="notice error" role="alert">
                  Stock insuficiente. Reduce la cantidad o actualiza las
                  existencias antes de confirmar.
                </div>
              )}
              {duplicate && (
                <div className="notice error" role="alert">
                  Cada producto debe aparecer una sola vez.
                </div>
              )}
              {priceLoading && <p role="status">Cargando precios…</p>}
              {!priceLoading && missingPrice && (
                <div className="notice error" role="alert">
                  Un producto no tiene precio en esta lista. Selecciona otra
                  lista o usa precio manual.
                </div>
              )}
              {priceError && (
                <div className="notice error" role="alert">
                  {priceError}
                </div>
              )}
              <div className="purchase-total">
                <span>Total estimado</span>
                <strong>{amount(estimate)}</strong>
              </div>
              <div className="notice">
                Al confirmar, el servidor validará nuevamente el stock,
                calculará el total definitivo y registrará la salida con fecha y
                responsable. La venta no puede editarse ni eliminarse.
              </div>
            </>
          )}
          {error && (
            <div className="notice error" role="alert">
              {error}
            </div>
          )}
        </div>
        <footer>
          <button
            type="button"
            className="secondary"
            disabled={busy}
            onClick={onClose}
          >
            {saleId ? "Cerrar comprobante" : "Cancelar"}
          </button>
          {!saleId && (
            <button
              className="primary"
              disabled={
                busy ||
                insufficient ||
                missingPrice ||
                duplicate ||
                priceLoading ||
                Boolean(priceError) ||
                uncertain
              }
            >
              {busy ? "Registrando…" : "Confirmar venta"}
            </button>
          )}
        </footer>
      </form>
    </dialog>
  );
}
