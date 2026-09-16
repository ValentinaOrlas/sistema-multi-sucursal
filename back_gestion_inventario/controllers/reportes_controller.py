"""Coordina los casos de uso de reportes."""

from service import reportes_service as service


def dashboard(db, user, sucursal_id):
    return service.dashboard(db, user, sucursal_id)


def demanda(db, user, sucursal_id, dias):
    return service.demanda(db, user, sucursal_id, dias)


def logistica(db, user, sucursal_id, dias, ordenar_por):
    return service.logistica(db, user, sucursal_id, dias, ordenar_por)
