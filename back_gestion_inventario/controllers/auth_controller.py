"""Coordina los casos de uso de auth."""

from service import auth_service as service


def login(payload, db):
    return service.login(payload, db)


def me(user):
    return service.me(user)
