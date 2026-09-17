import { useEffect, useRef, useState } from "react";
import { api, number, amount } from "./api";
import Icon from "./Icons";

function Field({ label, children, hint, ...props }) {
  return (
    <label>
      {label}
      {children || <input {...props} />} {hint && <small>{hint}</small>}
    </label>
  );
}
export default function InventoryForm({
  modal,
  categories,
  products,
  branch,
  user,
  onClose,
  onSaved,
}) {
  const dialog = useRef(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [kind, setKind] = useState("INGRESO");
  const type = modal.type;
  const product = modal.product || {};
  const titles = {
    create: "Nuevo producto",
    edit: "Editar producto",
    view: "Detalle del producto",
    delete: "Eliminar producto",
    move: "Registrar movimiento",
    minimum: "Configurar stock mínimo",
    category: "Nueva categoría",
  };
  useEffect(() => {
    const el = dialog.current;
    const previous = document.activeElement;
    el.showModal();
    return () => {
      el.close();
      previous?.focus();
    };
  }, []);
  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const data = Object.fromEntries(new FormData(event.currentTarget));
    let path;
    let body;
    let method = "POST";
    if (type === "create") {
      path = "/inventario/productos";
      body = { ...data, categoria_id: Number(data.categoria_id) };
    } else if (type === "edit") {
      path = `/inventario/productos/${product.id}`;
      method = "PATCH";
      body = { ...data, categoria_id: Number(data.categoria_id) };
    } else if (type === "delete") {
      path = `/inventario/productos/${product.id}`;
      method = "DELETE";
    } else if (type === "minimum") {
      path = "/inventario";
      body = {
        sucursal_id: Number(branch.id),
        producto_id: product.id,
        stock_minimo_local: data.stock_minimo_local,
      };
    } else if (type === "category") {
      path = "/categorias";
      body = data;
    } else {
      path = "/inventario/movimientos";
      body = {
        sucursal_id: Number(branch.id),
        producto_id: Number(data.producto_id),
        tipo_movimiento: kind,
        cantidad: data.cantidad,
        motivo: `${data.razon}: ${data.detalle.trim()}`,
      };
      if (kind === "INGRESO") body.costo_unitario = data.costo_unitario;
      if (body.motivo.length > 100) {
        setError("El motivo completo no puede superar 100 caracteres.");
        setBusy(false);
        return;
      }
    }
    try {
      await api(path, { method, body });
      onSaved(
        type === "delete"
          ? "Producto eliminado."
          : type === "move"
            ? "Movimiento registrado. El stock y el historial fueron actualizados."
            : "Cambios guardados correctamente.",
      );
    } catch (e) {
      setError(
        type === "delete" && e.message.includes("restricción")
          ? "No se puede eliminar este producto porque tiene inventario, movimientos o documentos asociados. Su historial debe conservarse."
          : e.message,
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <dialog
      ref={dialog}
      className="modal"
      aria-labelledby="inventory-dialog-title"
      onCancel={(event) => {
        event.preventDefault();
        if (!busy) onClose();
      }}
    >
      <header>
        <div>
          <span className="section-kicker">GESTIÓN DE INVENTARIO</span>
          <h2 id="inventory-dialog-title">{titles[type]}</h2>
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
      <form onSubmit={submit}>
        <div className="modal-body">
          {type === "view" ? (
            <>
              <div className="product-detail">
                <span className="product-symbol large">
                  <Icon name="laptop" size={32} />
                </span>
                <div>
                  <code>{product.sku}</code>
                  <h3>{product.nombre}</h3>
                  <span>
                    {categories.find((c) => c.id === product.categoria_id)
                      ?.nombre || "Sin categoría"}
                  </span>
                </div>
              </div>
              <p className="description">
                {product.descripcion ||
                  "Este producto aún no tiene descripción."}
              </p>
              <dl className="detail-grid">
                <div>
                  <dt>Unidad de medida</dt>
                  <dd>{product.unidad_medida}</dd>
                </div>
                <div>
                  <dt>Sucursal consultada</dt>
                  <dd>{branch?.nombre || "Sin sucursal"}</dd>
                </div>
                <div>
                  <dt>Stock disponible</dt>
                  <dd>
                    {modal.stock
                      ? number(modal.stock.stock_actual)
                      : "Sin registro"}
                  </dd>
                </div>
                <div>
                  <dt>Stock mínimo</dt>
                  <dd>
                    {modal.stock
                      ? number(modal.stock.stock_minimo_local)
                      : "Sin configurar"}
                  </dd>
                </div>
                <div>
                  <dt>Costo promedio unitario</dt>
                  <dd>
                    {modal.stock
                      ? amount(modal.stock.costo_promedio_ponderado)
                      : "—"}
                  </dd>
                </div>
              </dl>
            </>
          ) : type === "delete" ? (
            <>
              <div className="delete-symbol">
                <Icon name="trash" size={28} />
              </div>
              <h3>¿Eliminar “{product.nombre}”?</h3>
              <p>
                Se eliminará del catálogo general de la red. Esta acción no
                puede deshacerse.
              </p>
              <div className="notice">
                Solo es posible eliminar productos sin inventario ni historial
                asociado.
              </div>
            </>
          ) : type === "category" ? (
            <>
              <Field
                label="Nombre"
                name="nombre"
                required
                maxLength={100}
                placeholder="Ej. Memorias RAM"
              />
              <Field label="Descripción">
                <textarea name="descripcion" rows={3} />
              </Field>
            </>
          ) : type === "minimum" ? (
            <>
              <p>
                Configura el umbral de reabastecimiento de{" "}
                <strong>{product.nombre}</strong> en{" "}
                <strong>{branch.nombre}</strong>.
              </p>
              <Field
                label="Stock mínimo local"
                name="stock_minimo_local"
                type="number"
                required
                min="0"
                max="99999999999.999"
                step="0.001"
                defaultValue={modal.stock?.stock_minimo_local || "0"}
              />
              <div className="notice">
                Se mostrará una alerta cuando el stock sea igual o inferior al
                mínimo.
              </div>
            </>
          ) : type === "move" ? (
            <>
              <div className="notice">
                <Icon name="branch" size={17} />
                <span>
                  Sucursal: <strong>{branch.nombre}</strong> · Responsable:{" "}
                  <strong>{user.nombre}</strong>
                </span>
              </div>
              <Field label="Producto">
                <select
                  name="producto_id"
                  required
                  defaultValue={product.id || ""}
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
              </Field>
              <div className="form-grid">
                <Field label="Tipo de movimiento">
                  <select
                    value={kind}
                    onChange={(e) => setKind(e.target.value)}
                  >
                    <option value="INGRESO">Entrada de inventario</option>
                    <option value="RETIRO">Salida de inventario</option>
                  </select>
                </Field>
                <Field
                  label="Cantidad en unidad base"
                  name="cantidad"
                  type="number"
                  step="0.001"
                  min="0.001"
                  max="99999999999.999"
                  required
                />
              </div>
              {kind === "INGRESO" && (
                <Field
                  label="Costo unitario"
                  name="costo_unitario"
                  type="number"
                  step="0.01"
                  min="0"
                  max="9999999999.99"
                  required
                  hint="Costo por unidad base. Se recalcula el costo promedio del inventario."
                />
              )}
              <Field label="Motivo">
                <select name="razon" key={kind}>
                  {(kind === "INGRESO"
                    ? ["Compra", "Devolución", "Ajuste de inventario"]
                    : ["Venta", "Merma", "Ajuste de inventario"]
                  ).map((x) => (
                    <option key={x}>{x}</option>
                  ))}
                </select>
              </Field>
              <Field
                label="Detalle del motivo"
                name="detalle"
                required
                maxLength={75}
                placeholder="Ej. Recepción de dispositivos revisados"
              />
              <small>
                La fecha y el responsable se registran automáticamente. Las
                salidas se validan contra el stock disponible.
              </small>
            </>
          ) : (
            <>
              {type === "create" && (
                <div className="notice">
                  <Icon name="branch" size={17} />
                  <span>
                    El inventario inicial se registrará en{" "}
                    <strong>{branch?.nombre}</strong>, tu sucursal asignada.
                  </span>
                </div>
              )}
              <div className="form-grid">
                <Field
                  label="SKU único"
                  name="sku"
                  defaultValue={product.sku}
                  required
                  maxLength={100}
                  placeholder="TEC-LAP-001"
                />
                <Field
                  label="Nombre del producto"
                  name="nombre"
                  defaultValue={product.nombre}
                  required
                  maxLength={150}
                  placeholder="Laptop Lenovo ThinkPad"
                />
              </div>
              <Field label="Descripción">
                <textarea
                  name="descripcion"
                  defaultValue={product.descripcion || ""}
                  maxLength={5000}
                  rows={3}
                  placeholder="Características, modelo y especificaciones técnicas"
                />
              </Field>
              <div className="form-grid">
                <Field label="Categoría">
                  <select
                    name="categoria_id"
                    defaultValue={product.categoria_id || ""}
                    required
                  >
                    <option value="" disabled>
                      Selecciona una categoría
                    </option>
                    {categories.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.nombre}
                      </option>
                    ))}
                  </select>
                </Field>
                <Field
                  label="Unidad de medida"
                  name={type === "create" ? "unidad_medida" : undefined}
                  defaultValue={product.unidad_medida || "unidad"}
                  required
                  maxLength={50}
                  readOnly={type === "edit"}
                  hint={
                    type === "edit"
                      ? "La unidad base se conserva para proteger el historial."
                      : "Ej. unidad, kit, metro"
                  }
                />
              </div>
              {type === "create" && (
                <>
                  <div className="form-divider">EXISTENCIAS INICIALES</div>
                  <div className="form-grid">
                    <Field
                      label="Cantidad inicial"
                      name="cantidad_inicial"
                      type="number"
                      required
                      min="0.001"
                      step="0.001"
                      max="99999999999.999"
                    />
                    <Field
                      label="Stock mínimo"
                      name="stock_minimo"
                      type="number"
                      required
                      min="0"
                      step="0.001"
                      max="99999999999.999"
                      defaultValue="0"
                    />
                  </div>
                  <Field
                    label="Costo unitario"
                    name="costo_unitario"
                    type="number"
                    required
                    min="0"
                    step="0.000001"
                    max="999999999999.999999"
                  />
                  <small>
                    El ingreso inicial conservará la fecha, tu identidad, la
                    cantidad y el motivo de registro.
                  </small>
                </>
              )}
              {type === "edit" && (
                <div className="notice">
                  Los atributos del producto son compartidos por todas las
                  sucursales. El stock se modifica mediante movimientos.
                </div>
              )}
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
            onClick={onClose}
            disabled={busy}
          >
            {type === "view" ? "Cerrar" : "Cancelar"}
          </button>
          {type !== "view" && (
            <button
              className={type === "delete" ? "danger" : "primary"}
              disabled={busy}
            >
              {busy
                ? "Guardando…"
                : type === "delete"
                  ? "Confirmar eliminación"
                  : type === "create"
                    ? "Registrar producto"
                    : type === "move"
                      ? "Confirmar movimiento"
                      : "Guardar cambios"}
            </button>
          )}
        </footer>
      </form>
    </dialog>
  );
}
