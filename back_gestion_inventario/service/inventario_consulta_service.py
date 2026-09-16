from core.dependencies import branch_access
from dtos import schemas as s
from models import InventarioSucursalModel, MovimientosInventarioModel, ProductoModel
from repositories import inventario_repository as repo

from service.inventario_service import (
    lock_branches,
    move,
    normalize,
    require,
    stock,
)


def listado(
    db,
    user,
    sucursal_id: int | None = None,
    producto_id: int | None = None,
    offset: int = 0,
    limit: int = 100,
):
    return repo.inventory(
        db, InventarioSucursalModel, sucursal_id, producto_id, offset, limit
    )


def configurar(payload: s.InventarioSucursalCreate, db, user):
    branch_access(user, payload.sucursal_id, manager=True)
    lock_branches(db, payload.sucursal_id)
    require(db, ProductoModel, payload.producto_id)
    obj = stock(db, payload.sucursal_id, payload.producto_id)
    obj.stock_minimo_local = payload.stock_minimo_local
    repo.save(db, obj)
    return obj


def registrar(payload: s.MovimientoCreate, db, user):
    branch_access(user, payload.sucursal_id)
    lock_branches(db, payload.sucursal_id)
    quantity, factor = normalize(
        db, payload.producto_id, payload.cantidad, payload.unidad_id
    )
    return move(
        db,
        user,
        payload.sucursal_id,
        payload.producto_id,
        quantity,
        payload.tipo_movimiento,
        payload.motivo,
        payload.costo_unitario / factor if payload.costo_unitario is not None else None,
    )


def movimientos(
    db,
    user,
    sucursal_id: int | None = None,
    producto_id: int | None = None,
    offset: int = 0,
    limit: int = 100,
):
    if user.rol.nombre != "ADMIN_GENERAL":
        sucursal_id = sucursal_id or user.sucursal_id
        branch_access(user, sucursal_id)
    return repo.inventory(
        db,
        MovimientosInventarioModel,
        sucursal_id,
        producto_id,
        offset,
        limit,
        descending=True,
    )


def alertas(db, user, sucursal_id: int | None = None):
    return repo.inventory(db, InventarioSucursalModel, sucursal_id, alerts=True)
