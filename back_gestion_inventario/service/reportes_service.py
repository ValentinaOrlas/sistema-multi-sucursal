from datetime import datetime, timedelta, timezone
from decimal import Decimal

from core.dependencies import branch_access
from repositories import reportes_repository as repo


def scope(user, branch):
    if user.rol.nombre != "ADMIN_GENERAL":
        branch = branch or user.sucursal_id
        branch_access(user, branch)
    return branch


def dashboard(db, user, sucursal_id: int | None = None):
    branch = scope(user, sucursal_id)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    monthly = []
    year, month = now.year, now.month
    for _ in range(4):
        start = datetime(year, month, 1)
        end = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)
        count, total = repo.monthly_sales(db, start, end, branch)
        monthly.append(
            {"mes": start.strftime("%Y-%m"), "ventas": count, "importe": total}
        )
        year, month = (year - 1, 12) if month == 1 else (year, month - 1)
    stocks = repo.stocks(db, branch)
    active = repo.active_transfers(db, branch)
    comparison = []
    if user.rol.nombre == "ADMIN_GENERAL":
        start = datetime(now.year, now.month, 1)
        end = (
            datetime(now.year + 1, 1, 1)
            if now.month == 12
            else datetime(now.year, now.month + 1, 1)
        )
        comparison = [
            {"sucursal_id": bid, "importe": total, "ventas": count}
            for bid, total, count in repo.comparison(db, start, end)
        ]
    return {
        "zona_horaria": "UTC",
        "ventas_mensuales": monthly,
        "valor_inventario": sum(
            (x.stock_actual * x.costo_promedio_ponderado for x in stocks), Decimal(0)
        ),
        "productos_por_reabastecer": [
            {
                "sucursal_id": x.sucursal_id,
                "producto_id": x.producto_id,
                "stock": x.stock_actual,
                "minimo": x.stock_minimo_local,
            }
            for x in stocks
            if x.stock_actual <= x.stock_minimo_local
        ],
        "transferencias_activas": [
            {
                "id": x.id,
                "estado": x.estado,
                "origen": x.sucursal_origen_id,
                "destino": x.sucursal_destino_id,
                "productos": [
                    {
                        "producto_id": d.producto_id,
                        "cantidad_en_transito": d.cantidad_enviada
                        if x.estado == "EN_TRANSITO"
                        else 0,
                        "faltantes": d.faltantes,
                    }
                    for d in x.detalles
                ],
            }
            for x in active
        ],
        "comparativa_sucursales": comparison,
        "demanda": demanda(db, user, branch, 30),
    }


def demanda(
    db,
    user,
    sucursal_id: int | None = None,
    dias: int = 30,
):
    branch = scope(user, sucursal_id)
    since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=dias)
    sales, changes = repo.demand_totals(db, since, branch)
    volumes = {(bid, pid): Decimal(str(qty)) for bid, pid, qty in sales}
    deltas = {(bid, pid): Decimal(str(qty)) for bid, pid, qty in changes}
    result = []
    for row in repo.stocks(db, branch):
        key = (row.sucursal_id, row.producto_id)
        sold = volumes.get(key, Decimal(0))
        daily = sold / dias
        opening = row.stock_actual - deltas.get(key, Decimal(0))
        average = (opening + row.stock_actual) / 2
        result.append(
            {
                "sucursal_id": row.sucursal_id,
                "producto_id": row.producto_id,
                "dias_observados": dias,
                "unidades_vendidas": sold,
                "promedio_diario": daily,
                "demanda_estimada_30_dias": daily * 30,
                "dias_cobertura": row.stock_actual / daily if daily else None,
                "rotacion_aproximada": sold / average if average > 0 else None,
                "metodo": "Promedio móvil; rotación con promedio de stock inicial y final",
            }
        )
    return sorted(result, key=lambda x: x["unidades_vendidas"], reverse=True)


def logistica(
    db,
    user,
    sucursal_id: int | None = None,
    dias: int = 90,
    ordenar_por: str = "prioridad",
):
    branch = scope(user, sucursal_id)
    since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=dias)
    details = []
    for row in repo.logistics(db, since, branch):
        details.append(
            {
                "id": row.id,
                "ruta": row.ruta,
                "origen": row.sucursal_origen_id,
                "destino": row.sucursal_destino_id,
                "prioridad": row.prioridad,
                "costo_envio": row.costo_envio,
                "estado": row.estado,
                "horas_estimadas": (
                    row.fecha_estimada_llegada - row.fecha_despacho
                ).total_seconds()
                / 3600
                if row.fecha_estimada_llegada
                else None,
                "horas_reales": (
                    row.fecha_real_llegada - row.fecha_despacho
                ).total_seconds()
                / 3600
                if row.fecha_real_llegada
                else None,
                "a_tiempo": row.fecha_real_llegada <= row.fecha_estimada_llegada
                if row.fecha_real_llegada and row.fecha_estimada_llegada
                else None,
            }
        )
    priorities = {"ALTA": 0, "MEDIA": 1, "BAJA": 2}
    if ordenar_por == "prioridad":
        details.sort(key=lambda x: (priorities[x["prioridad"]], x["id"]))
    elif ordenar_por == "costo":
        details.sort(key=lambda x: (x["costo_envio"], x["id"]))
    else:
        details.sort(
            key=lambda x: (
                x["horas_estimadas"] is None,
                x["horas_estimadas"] or 0,
                x["id"],
            )
        )
    groups = {}
    for item in details:
        key = (item["origen"], item["destino"], item["ruta"])
        group = groups.setdefault(
            key,
            {
                "origen": key[0],
                "destino": key[1],
                "ruta": key[2],
                "envios": 0,
                "recibidos": 0,
                "a_tiempo": 0,
                "costo_total": Decimal(0),
            },
        )
        group["envios"] += 1
        group["costo_total"] += item["costo_envio"]
        if item["a_tiempo"] is not None:
            group["recibidos"] += 1
            group["a_tiempo"] += int(item["a_tiempo"])
    return {"dias": dias, "rutas": list(groups.values()), "transferencias": details}
