"""Coordina los casos de uso de inventario."""

from service import inventario_consulta_service as service


def listado(db, user, sucursal_id, producto_id, offset, limit):
    return service.listado(db, user, sucursal_id, producto_id, offset, limit)


def configurar(payload, db, user):
    return service.configurar(payload, db, user)


def registrar(payload, db, user):
    return service.registrar(payload, db, user)


def movimientos(db, user, sucursal_id, producto_id, offset, limit):
    return service.movimientos(db, user, sucursal_id, producto_id, offset, limit)


def alertas(db, user, sucursal_id):
    return service.alertas(db, user, sucursal_id)
