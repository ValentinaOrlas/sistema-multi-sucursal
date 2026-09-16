"""Coordina los casos de uso de catalogos."""

from service import catalogos_service as service


def roles(db, user):
    return service.roles(db, user)


def usuarios(db, user, offset, limit):
    return service.usuarios(db, user, offset, limit)


def crear_usuario(payload, db, user):
    return service.crear_usuario(payload, db, user)


def editar_usuario(identity, payload, db, user):
    return service.editar_usuario(identity, payload, db, user)


def unidades(identity, db, user):
    return service.unidades(identity, db, user)


def crear_unidad(identity, payload, db, user):
    return service.crear_unidad(identity, payload, db, user)


def listas(db, user):
    return service.listas(db, user)


def crear_lista(payload, db, user):
    return service.crear_lista(payload, db, user)


def precios(identity, db, user):
    return service.precios(identity, db, user)


def guardar_precio(identity, payload, db, user):
    return service.guardar_precio(identity, payload, db, user)


def list_rows(model, db, user, offset, limit):
    return service.list_rows(model, db, user, offset, limit)


def get_row(model, identity, db, user):
    return service.get_row(model, identity, db, user)


def create_row(model, payload, db, user):
    return service.create_row(model, payload, db, user)


def update_row(model, identity, payload, db, user):
    return service.update_row(model, identity, payload, db, user)


def delete_row(model, identity, db, user):
    return service.delete_row(model, identity, db, user)
