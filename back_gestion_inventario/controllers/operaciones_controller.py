"""Coordina los casos de uso de operaciones."""

from service import operaciones_consulta_service as service


def crear_venta(payload, db, user):
    return service.crear_venta(payload, db, user)


def ventas(db, user, sucursal_id, offset, limit):
    return service.ventas(db, user, sucursal_id, offset, limit)


def venta(identity, db, user):
    return service.venta(identity, db, user)


def crear_compra(payload, db, user):
    return service.crear_compra(payload, db, user)


def compras(db, user, sucursal_id, proveedor_id, producto_id, offset, limit):
    return service.compras(
        db, user, sucursal_id, proveedor_id, producto_id, offset, limit
    )


def compra(identity, db, user):
    return service.compra(identity, db, user)


def recibir_compra(identity, db, user):
    return service.recibir_compra(identity, db, user)


def cancelar_compra(identity, db, user):
    return service.cancelar_compra(identity, db, user)


def crear_transferencia(payload, db, user):
    return service.crear_transferencia(payload, db, user)


def transferencias(db, user, estado, offset, limit):
    return service.transferencias(db, user, estado, offset, limit)


def transferencia(identity, db, user):
    return service.transferencia(identity, db, user)


def preparar(identity, payload, db, user):
    return service.preparar(identity, payload, db, user)


def despachar(identity, payload, db, user):
    return service.despachar(identity, payload, db, user)


def recibir(identity, payload, db, user):
    return service.recibir(identity, payload, db, user)


def cancelar(identity, db, user):
    return service.cancelar(identity, db, user)
