from core.dependencies import branch_access
from dtos import schemas as s
from fastapi import HTTPException
from models import (
    OrdenCompraModel,
    TransferenciaModel,
    VentaModel,
)
from repositories import inventario_repository as repo

from service import operaciones_service as ops
from service.inventario_service import require


def crear_venta(payload: s.VentaCreate, db, user):
    return ops.create_sale(db, user, payload)


def ventas(
    db,
    user,
    sucursal_id: int | None = None,
    offset: int = 0,
    limit: int = 100,
):
    if user.rol.nombre != "ADMIN_GENERAL":
        sucursal_id = sucursal_id or user.sucursal_id
        branch_access(user, sucursal_id)
    return repo.documents(
        db, VentaModel, branch=sucursal_id, offset=offset, limit=limit
    )


def venta(identity: int, db, user):
    obj = require(db, VentaModel, identity)
    branch_access(user, obj.sucursal_id)
    return obj


def crear_compra(payload: s.OrdenCompraCreate, db, user):
    return ops.create_purchase(db, user, payload)


def compras(
    db,
    user,
    sucursal_id: int | None = None,
    proveedor_id: int | None = None,
    producto_id: int | None = None,
    offset: int = 0,
    limit: int = 100,
):
    if user.rol.nombre != "ADMIN_GENERAL":
        sucursal_id = sucursal_id or user.sucursal_id
        branch_access(user, sucursal_id)
    return repo.documents(
        db,
        OrdenCompraModel,
        branch=sucursal_id,
        offset=offset,
        limit=limit,
        supplier=proveedor_id,
        product=producto_id,
    )


def compra(identity: int, db, user):
    obj = require(db, OrdenCompraModel, identity)
    branch_access(user, obj.sucursal_destino_id)
    return obj


def recibir_compra(identity: int, db, user):
    return ops.receive_purchase(db, user, identity)


def cancelar_compra(identity: int, db, user):
    obj = ops.locked(db, OrdenCompraModel, identity)
    branch_access(user, obj.sucursal_destino_id, manager=True)
    ops.state(obj, "PENDIENTE")
    obj.estado = "CANCELADA"
    repo.save(db, obj)
    return obj


def crear_transferencia(payload: s.TransferenciaCreate, db, user):
    return ops.create_transfer(db, user, payload)


def transferencias(
    db,
    user,
    estado: str | None = None,
    offset: int = 0,
    limit: int = 100,
):
    branch = user.sucursal_id if user.rol.nombre != "ADMIN_GENERAL" else None
    return repo.documents(
        db, TransferenciaModel, branch=branch, status=estado, offset=offset, limit=limit
    )


def transferencia(identity: int, db, user):
    obj = require(db, TransferenciaModel, identity)
    if user.rol.nombre != "ADMIN_GENERAL" and user.sucursal_id not in (
        obj.sucursal_origen_id,
        obj.sucursal_destino_id,
    ):
        raise HTTPException(403, "La transferencia no corresponde a tu sucursal")
    return obj


def preparar(identity: int, payload: s.PrepararTransferencia, db, user):
    return ops.prepare_transfer(db, user, identity, payload)


def despachar(identity: int, payload: s.DespacharTransferencia, db, user):
    return ops.dispatch_transfer(db, user, identity, payload)


def recibir(identity: int, payload: s.RecibirTransferencia, db, user):
    return ops.receive_transfer(db, user, identity, payload)


def cancelar(identity: int, db, user):
    obj = ops.locked(db, TransferenciaModel, identity)
    branch_access(user, obj.sucursal_destino_id, manager=True)
    if obj.estado not in {"SOLICITADA", "PREPARADA"}:
        raise HTTPException(409, "Solo se puede cancelar antes del despacho")
    obj.estado = "CANCELADA"
    repo.save(db, obj)
    return obj
