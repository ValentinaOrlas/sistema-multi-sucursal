import { useEffect, useRef, useState } from "react";
import { api, amount, date, number, purchaseTotal } from "./api";
import Icon from "./Icons";

const blankLine = () => ({
  key: crypto.randomUUID(),
  producto_id: "",
  cantidad: "1",
  precio_unitario: "",
  descuento: "0",
});
export default function PurchaseForm({
  mode,
  orderId,
  supplier,
  suppliers,
  products,
  branch,
  user,
  onClose,
  onSaved,
}) {
  const ref = useRef(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [order, setOrder] = useState(null);
  const [lines, setLines] = useState([blankLine()]);
  const [confirmation, setConfirmation] = useState("");
  const admin = user.rol.nombre === "ADMIN_GENERAL";
  const manager = admin || user.rol.nombre === "GERENTE_SUCURSAL";
  const total = purchaseTotal({ detalles: lines });
  useEffect(() => {
    const element = ref.current;
    const previous = document.activeElement;
    element.showModal();
    const controller = new AbortController();
    if (orderId)
      api(`/compras/${orderId}`, { signal: controller.signal })
        .then(setOrder)
        .catch((e) => {
          if (!controller.signal.aborted) setError(e.message);
        });
    return () => {
      controller.abort();
      element.close();
      previous?.focus();
    };
  }, [orderId]);
  function update(key, field, value) {
    setLines((old) =>
      old.map((line) =>
        line.key === key ? { ...line, [field]: value } : line,
      ),
    );
  }
  async function save(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const values = Object.fromEntries(new FormData(event.currentTarget));
    try {
      if (mode === "supplier") {
        await api(supplier ? `/proveedores/${supplier.id}` : "/proveedores", {
          method: supplier ? "PATCH" : "POST",
          body: {
            ...values,
            tiempo_entrega_promedio_dias: Number(
              values.tiempo_entrega_promedio_dias,
            ),
          },
        });
        onSaved("Proveedor guardado.");
      } else if (mode === "create") {
        if (new Set(lines.map((x) => x.producto_id)).size !== lines.length)
          throw new Error("Incluye cada producto una sola vez en la orden.");
        await api("/compras", {
          method: "POST",
          body: {
            proveedor_id: Number(values.proveedor_id),
            sucursal_destino_id: branch.id,
            plazo_pago_dias: Number(values.plazo_pago_dias),
            detalles: lines.map(({ key: _key, ...line }) => ({
              ...line,
              producto_id: Number(line.producto_id),
            })),
          },
        });
        onSaved(
          "Orden creada. El stock se actualizará cuando confirmes la recepción.",
        );
      } else {
        if (!confirmation) return;
        await api(`/compras/${order.id}/${confirmation}`, { method: "POST" });
        onSaved(
          confirmation === "recibir"
            ? "Compra recibida: existencias, costo promedio e historial actualizados."
            : "Orden cancelada. El inventario no ha cambiado.",
        );
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  const names = new Map(products.map((p) => [p.id, p]));
  return (
    <dialog
      ref={ref}
      className={`modal ${mode !== "supplier" ? "purchase-modal" : ""}`}
      aria-labelledby="purchase-title"
      onCancel={(e) => {
        e.preventDefault();
        if (!busy) onClose();
      }}
    >
      <header>
        <div>
          <span className="section-kicker">ABASTECIMIENTO DE TECNOLOGÍA</span>
          <h2 id="purchase-title">
            {mode === "supplier"
              ? supplier
                ? "Editar proveedor"
                : "Nuevo proveedor"
              : mode === "create"
                ? "Nueva orden de compra"
                : `Orden de compra #${orderId}`}
          </h2>
        </div>
        <button
          type="button"
          className="icon-button"
          aria-label="Cerrar ventana"
          onClick={onClose}
          disabled={busy}
        >
          <Icon name="close" />
        </button>
      </header>
      <form onSubmit={save}>
        <div className="modal-body">
          {mode === "supplier" ? (
            <>
              <label>
                Nombre del proveedor
                <input
                  name="nombre"
                  required
                  maxLength={150}
                  defaultValue={supplier?.nombre}
                />
              </label>
              <label>
                Contacto
                <input
                  name="contacto"
                  maxLength={100}
                  defaultValue={supplier?.contacto || ""}
                  placeholder="Correo o teléfono"
                />
              </label>
              <label>
                Condiciones comerciales
                <textarea
                  name="condiciones_comerciales"
                  rows={3}
                  defaultValue={supplier?.condiciones_comerciales || ""}
                />
              </label>
              <label>
                Tiempo de entrega promedio (días)
                <input
                  name="tiempo_entrega_promedio_dias"
                  type="number"
                  min="0"
                  max="2147483647"
                  step="1"
                  required
                  defaultValue={supplier?.tiempo_entrega_promedio_dias || 0}
                />
              </label>
            </>
          ) : mode === "create" ? (
            <>
              <div className="notice">
                <Icon name="branch" size={18} />
                Mercancía para <strong>{branch.nombre}</strong>. Responsable:{" "}
                {user.nombre}.
              </div>
              <div className="form-grid">
                <label>
                  Proveedor
                  <select name="proveedor_id" required defaultValue="">
                    <option value="" disabled>
                      Selecciona un proveedor
                    </option>
                    {suppliers.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.nombre}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Plazo de pago (días)
                  <input
                    name="plazo_pago_dias"
                    type="number"
                    min="0"
                    max="2147483647"
                    step="1"
                    required
                    defaultValue="0"
                  />
                </label>
              </div>
              <div className="form-divider">PRODUCTOS DE LA ORDEN</div>
              {lines.map((line, index) => (
                <fieldset className="purchase-line" key={line.key}>
                  <legend>Producto {index + 1}</legend>
                  <label>
                    Producto tecnológico
                    <select
                      value={line.producto_id}
                      onChange={(e) =>
                        update(line.key, "producto_id", e.target.value)
                      }
                      required
                    >
                      <option value="" disabled>
                        Selecciona un producto
                      </option>
                      {products.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.sku} · {p.nombre} ({p.unidad_medida})
                        </option>
                      ))}
                    </select>
                  </label>
                  <div className="purchase-line-values">
                    <label>
                      Cantidad
                      <input
                        type="number"
                        min="0.001"
                        max="99999999999.999"
                        step="0.001"
                        required
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
                        min="0"
                        max="9999999999.99"
                        step="0.01"
                        required
                        value={line.precio_unitario}
                        onChange={(e) =>
                          update(line.key, "precio_unitario", e.target.value)
                        }
                      />
                    </label>
                    <label>
                      Descuento (%)
                      <input
                        type="number"
                        min="0"
                        max="100"
                        step="0.01"
                        required
                        value={line.descuento}
                        onChange={(e) =>
                          update(line.key, "descuento", e.target.value)
                        }
                      />
                    </label>
                    <button
                      className="icon-button delete-action"
                      aria-label={`Quitar producto ${index + 1}`}
                      type="button"
                      disabled={lines.length === 1}
                      onClick={() =>
                        setLines((old) => old.filter((x) => x.key !== line.key))
                      }
                    >
                      <Icon name="trash" size={18} />
                    </button>
                  </div>
                  <small>
                    Cantidad y precio por{" "}
                    {names.get(Number(line.producto_id))?.unidad_medida ||
                      "unidad base"}
                    .
                  </small>
                </fieldset>
              ))}
              <button
                type="button"
                className="secondary"
                onClick={() => setLines((old) => [...old, blankLine()])}
                disabled={lines.length >= 100}
              >
                <Icon name="plus" size={16} />
                Agregar producto
              </button>
              <div className="purchase-total">
                <span>Importe neto estimado</span>
                <strong>{amount(total)}</strong>
              </div>
              <small>
                Precios con descuento, sin impuestos adicionales. La creación de
                la orden no modifica las existencias.
              </small>
            </>
          ) : order ? (
            <>
              <div className="detail-grid">
                <div>
                  <small>Proveedor</small>
                  <p>
                    <strong>
                      {suppliers.find((s) => s.id === order.proveedor_id)
                        ?.nombre || `Proveedor #${order.proveedor_id}`}
                    </strong>
                  </p>
                </div>
                <div>
                  <small>Estado</small>
                  <p>
                    <span
                      className={`badge ${order.estado === "RECIBIDA" ? "ok" : order.estado === "CANCELADA" ? "empty" : "low"}`}
                    >
                      {order.estado}
                    </span>
                  </p>
                </div>
                <div>
                  <small>Creación</small>
                  <p>{date(order.fecha_creacion)}</p>
                </div>
                <div>
                  <small>Recepción</small>
                  <p>{date(order.fecha_recepcion)}</p>
                </div>
                <div>
                  <small>Plazo de pago</small>
                  <p>{order.plazo_pago_dias} días</p>
                </div>
                <div>
                  <small>Responsable de la orden</small>
                  <p>
                    {order.usuario_id === user.id
                      ? user.nombre
                      : `Usuario #${order.usuario_id}`}
                  </p>
                </div>
              </div>
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
                    {order.detalles.map((d) => (
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
                        <td>{number(d.descuento)} %</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="purchase-total">
                <span>Importe neto de los productos</span>
                <strong>{amount(purchaseTotal(order))}</strong>
              </div>
              {confirmation && (
                <div className="notice" role="status">
                  {confirmation === "recibir"
                    ? "Confirma únicamente si recibiste todos los productos indicados. Se sumarán las cantidades al stock de destino, se recalculará el costo promedio y se registrará el ingreso con tu identidad. No se puede repetir esta recepción."
                    : "La orden quedará cancelada y no podrá recibirse. No se modificarán existencias."}
                </div>
              )}
            </>
          ) : (
            <p role="status">
              {error ? "No se pudo cargar la orden." : "Consultando orden…"}
            </p>
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
            onClick={confirmation ? () => setConfirmation("") : onClose}
          >
            {confirmation ? "Volver" : "Cerrar"}
          </button>
          {mode === "create" || mode === "supplier" ? (
            <button className="primary" disabled={busy}>
              {busy
                ? "Guardando…"
                : mode === "create"
                  ? "Crear orden"
                  : "Guardar proveedor"}
            </button>
          ) : confirmation ? (
            <button
              className={confirmation === "cancelar" ? "danger" : "primary"}
              disabled={busy}
            >
              {busy
                ? "Procesando…"
                : confirmation === "recibir"
                  ? "Confirmar recepción completa"
                  : "Confirmar cancelación"}
            </button>
          ) : (
            order?.estado === "PENDIENTE" && (
              <>
                {manager && (
                  <button
                    type="button"
                    className="secondary"
                    onClick={() => setConfirmation("cancelar")}
                  >
                    Cancelar orden
                  </button>
                )}
                {branch?.activa && (
                  <button
                    type="button"
                    className="primary"
                    onClick={() => setConfirmation("recibir")}
                  >
                    Recibir mercancía
                  </button>
                )}
              </>
            )
          )}
        </footer>
      </form>
    </dialog>
  );
}
