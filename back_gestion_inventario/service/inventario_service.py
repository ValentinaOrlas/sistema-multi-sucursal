from decimal import ROUND_HALF_UP, Decimal

from fastapi import HTTPException
from models import (
    InventarioSucursalModel,
    MovimientosInventarioModel,
    ProductoModel,
    SucursalesModel,
    UnidadProductoModel,
)
from repositories import inventario_repository as repo

ZERO = Decimal(0)


def money(value):
    return Decimal(value).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)


def cost(value):
    return Decimal(value).quantize(Decimal(".000001"), rounding=ROUND_HALF_UP)


def require(db, model, identity):
    obj = repo.get(db, model, identity)
    if obj is None:
        raise HTTPException(
            404, f"{model.__tablename__}: registro {identity} no encontrado"
        )
    return obj


def lock_branches(db, *ids):
    # Lock existing branch rows in a fixed order, including when stock rows do not
    # exist yet. This serializes writes per branch and avoids first-insert races.
    for identity in sorted(set(ids)):
        branch = repo.get(db, SucursalesModel, identity, lock=True)
        if branch is None:
            raise HTTPException(404, "Sucursal no encontrada")
        if not branch.activa:
            raise HTTPException(409, "La sucursal está inactiva")


def normalize(db, product_id, quantity, unit_id=None):
    require(db, ProductoModel, product_id)
    factor = Decimal(1)
    if unit_id is not None:
        unit = require(db, UnidadProductoModel, unit_id)
        if unit.producto_id != product_id:
            raise HTTPException(422, "La unidad no pertenece al producto")
        factor = unit.factor
    value = quantity * factor
    if value != value.quantize(Decimal(".001")):
        raise HTTPException(
            422, "La conversión requiere más de 3 decimales de cantidad"
        )
    if value > Decimal("99999999999.999"):
        raise HTTPException(422, "Cantidad fuera de rango")
    return value, factor


def stock(db, branch_id, product_id):
    obj = repo.find(
        db,
        InventarioSucursalModel,
        lock=True,
        sucursal_id=branch_id,
        producto_id=product_id,
    )
    if obj is None:
        product = require(db, ProductoModel, product_id)
        obj = InventarioSucursalModel(
            sucursal_id=branch_id,
            producto_id=product_id,
            stock_actual=ZERO,
            stock_minimo_local=product.stock_minimo_global,
            costo_promedio_ponderado=ZERO,
        )
        repo.save(db, obj)
    return obj


def move(
    db, user, branch_id, product_id, quantity, kind, reason, unit_cost=None, **reference
):
    if quantity <= 0:
        raise HTTPException(422, "Cantidad debe ser positiva")
    obj = stock(db, branch_id, product_id)
    if kind == "RETIRO":
        if obj.stock_actual < quantity:
            raise HTTPException(
                409, f"Stock insuficiente para el producto {product_id}"
            )
        actual_cost = obj.costo_promedio_ponderado
        obj.stock_actual -= quantity
    else:
        actual_cost = cost(unit_cost)
        new_stock = obj.stock_actual + quantity
        obj.costo_promedio_ponderado = cost(
            (obj.stock_actual * obj.costo_promedio_ponderado + quantity * actual_cost)
            / new_stock
        )
        obj.stock_actual = new_stock
    row = MovimientosInventarioModel(
        sucursal_id=branch_id,
        producto_id=product_id,
        usuario_id=user.id,
        cantidad=quantity,
        tipo_movimiento=kind,
        motivo=reason,
        stock_resultante=obj.stock_actual,
        costo_unitario=actual_cost,
        **reference,
    )
    repo.save(db, obj)
    repo.save(db, row)
    return row
