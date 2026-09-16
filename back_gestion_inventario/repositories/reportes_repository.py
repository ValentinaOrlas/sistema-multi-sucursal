"""Consultas SQL de indicadores; fechas y filtros siempre parametrizados."""

from models import InventarioSucursalModel, TransferenciaModel
from sqlalchemy import text

from repositories.inventario_repository import inventory, rows


def monthly_sales(db, start, end, branch):
    return db.execute(
        text("""SELECT COUNT(*) AS ventas, COALESCE(SUM(total_venta), 0) AS importe
        FROM ventas WHERE fecha_venta >= :start AND fecha_venta < :end
        AND (:branch IS NULL OR sucursal_id = :branch)"""),
        {"start": start, "end": end, "branch": branch},
    ).one()


def comparison(db, start, end):
    return db.execute(
        text("""SELECT sucursal_id, SUM(total_venta), COUNT(*) FROM ventas
        WHERE fecha_venta >= :start AND fecha_venta < :end GROUP BY sucursal_id ORDER BY sucursal_id"""),
        {"start": start, "end": end},
    ).all()


def stocks(db, branch):
    return inventory(db, InventarioSucursalModel, branch)


def active_transfers(db, branch):
    return rows(
        db,
        TransferenciaModel,
        "estado IN ('SOLICITADA','PREPARADA','EN_TRANSITO','CON_FALTANTES') AND (:branch IS NULL OR sucursal_origen_id = :branch OR sucursal_destino_id = :branch)",
        {"branch": branch},
    )


def demand_totals(db, since, branch):
    params = {"since": since, "branch": branch}
    sales = db.execute(
        text("""SELECT v.sucursal_id, d.producto_id, SUM(d.cantidad)
        FROM ventas v JOIN detalle_venta d ON d.venta_id = v.id
        WHERE v.fecha_venta >= :since AND (:branch IS NULL OR v.sucursal_id = :branch)
        GROUP BY v.sucursal_id, d.producto_id"""),
        params,
    ).all()
    movements = db.execute(
        text("""SELECT sucursal_id, producto_id,
        SUM(CASE WHEN tipo_movimiento = 'INGRESO' THEN cantidad ELSE -cantidad END)
        FROM movimientos_inventario WHERE fecha_movimiento >= :since
        AND (:branch IS NULL OR sucursal_id = :branch) GROUP BY sucursal_id, producto_id"""),
        params,
    ).all()
    return sales, movements


def logistics(db, since, branch):
    return rows(
        db,
        TransferenciaModel,
        "fecha_despacho >= :since AND (:branch IS NULL OR sucursal_origen_id = :branch OR sucursal_destino_id = :branch)",
        {"since": since, "branch": branch},
    )
