"""SQL parametrizado. Los nombres de tablas y columnas provienen solo de los modelos.

Las entidades devueltas no se adjuntan a la sesión: guardar es explícito y ninguna
relación dispara consultas implícitas. El commit pertenece a la petición HTTP.
"""

from models import (
    Base,
    DetalleOrdenCompraModel,
    DetalleTransferenciaModel,
    DetalleVentaModel,
    OrdenCompraModel,
    RoleModel,
    SucursalesModel,
    TransferenciaModel,
    UsuarioModel,
    VentaModel,
)
from sqlalchemy import bindparam, text

DETAILS = {
    VentaModel: (DetalleVentaModel, "venta_id"),
    OrdenCompraModel: (DetalleOrdenCompraModel, "orden_compra_id"),
    TransferenciaModel: (DetalleTransferenciaModel, "transferencia_id"),
}


def table_for(model):
    if model not in {m.class_ for m in Base.registry.mappers}:
        raise ValueError("Modelo no permitido")
    return model.__table__


def rows(
    db, model, where="1=1", params=None, *, order="id", limit=None, offset=0, lock=False
):
    # where/order are internal SQL fragments, never values received from the API.
    table = table_for(model)
    values = dict(params or {})
    sql = f"SELECT * FROM {table.name} WHERE {where} ORDER BY {order}"
    if limit is not None:
        sql += " LIMIT :_limit OFFSET :_offset"
        values.update(_limit=limit, _offset=offset)
    if lock and db.bind.dialect.name == "postgresql":
        sql += " FOR UPDATE"
    statement = text(sql).columns(*table.columns)
    result = []
    for mapping in db.execute(statement, values).mappings():
        obj = model(**dict(mapping))
        if model is UsuarioModel:
            obj.rol = get(db, RoleModel, obj.rol_id)
            obj.sucursal = (
                get(db, SucursalesModel, obj.sucursal_id) if obj.sucursal_id else None
            )
        if model in DETAILS:
            detail, key = DETAILS[model]
            obj.detalles = rows(
                db, detail, f"{key} = :parent_id", {"parent_id": obj.id}
            )
        result.append(obj)
    return result


def get(db, model, identity, *, lock=False):
    result = rows(db, model, "id = :identity", {"identity": identity}, lock=lock)
    return result[0] if result else None


def find(db, model, *, lock=False, **filters):
    table = table_for(model)
    if not set(filters).issubset(table.columns.keys()):
        raise ValueError("Columna no permitida")
    result = rows(
        db,
        model,
        " AND ".join(f"{key} = :{key}" for key in filters) or "1=1",
        filters,
        lock=lock,
    )
    return result[0] if result else None


def save(db, obj):
    table = table_for(type(obj))
    values = {}
    for col in table.columns:
        if col.primary_key:
            continue
        value = getattr(obj, col.name)
        if value is None and obj.id is None:
            if col.default is not None:
                if not col.default.is_scalar:
                    raise ValueError("Default no escalar requiere valor explícito")
                value = col.default.arg
            elif col.server_default is not None:
                continue
        values[col.name] = value
    if obj.id is None:
        names = ", ".join(values)
        placeholders = ", ".join(f":{name}" for name in values)
        sql = f"INSERT INTO {table.name} ({names}) VALUES ({placeholders}) RETURNING *"
    else:
        sql = (
            f"UPDATE {table.name} SET "
            + ", ".join(f"{name} = :{name}" for name in values)
            + " WHERE id = :_id RETURNING *"
        )
        values["_id"] = obj.id
    statement = (
        text(sql)
        .bindparams(
            *(
                bindparam(name, type_=table.c[name].type)
                for name in values
                if name != "_id"
            )
        )
        .columns(*table.columns)
    )
    mapping = db.execute(statement, values).mappings().one()
    for name, value in mapping.items():
        setattr(obj, name, value)
    if type(obj) in DETAILS:
        _, key = DETAILS[type(obj)]
        for detail in obj.detalles:
            setattr(detail, key, obj.id)
            save(db, detail)
    if isinstance(obj, UsuarioModel):
        obj.rol = get(db, RoleModel, obj.rol_id)
        obj.sucursal = (
            get(db, SucursalesModel, obj.sucursal_id) if obj.sucursal_id else None
        )
    return obj


def delete(db, obj):
    table = table_for(type(obj))
    db.execute(
        text(f"DELETE FROM {table.name} WHERE id = :identity"), {"identity": obj.id}
    )


def inventory(
    db,
    model,
    branch=None,
    product=None,
    offset=0,
    limit=None,
    alerts=False,
    descending=False,
):
    filters = ["1=1"]
    values = {}
    if branch is not None:
        filters.append("sucursal_id = :branch")
        values["branch"] = branch
    if product is not None:
        filters.append("producto_id = :product")
        values["product"] = product
    if alerts:
        filters.append("stock_actual <= stock_minimo_local")
    return rows(
        db,
        model,
        " AND ".join(filters),
        values,
        order="id DESC" if descending else "id",
        limit=limit,
        offset=offset,
    )


def documents(
    db,
    model,
    branch=None,
    supplier=None,
    product=None,
    status=None,
    offset=0,
    limit=100,
):
    conditions = ["1=1"]
    params = {}
    if branch is not None:
        field = "sucursal_destino_id" if model is OrdenCompraModel else "sucursal_id"
        conditions.append(
            "(sucursal_origen_id = :branch OR sucursal_destino_id = :branch)"
            if model is TransferenciaModel
            else f"{field} = :branch"
        )
        params["branch"] = branch
    if supplier is not None:
        conditions.append("proveedor_id = :supplier")
        params["supplier"] = supplier
    if product is not None:
        conditions.append(
            "EXISTS (SELECT 1 FROM detalle_orden_compra d WHERE d.orden_compra_id = ordenes_compra.id AND d.producto_id = :product)"
        )
        params["product"] = product
    if status is not None:
        conditions.append("estado = :status")
        params["status"] = status
    return rows(
        db,
        model,
        " AND ".join(conditions),
        params,
        order="id DESC",
        limit=limit,
        offset=offset,
    )
