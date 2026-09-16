from typing import Annotated

from conection.conectionDb import getDb
from core.seguridad import Seguridad
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from models import UsuarioModel
from repositories import inventario_repository as repo
from sqlalchemy.orm import Session

Db = Annotated[Session, Depends(getDb, scope="function")]
bearer = HTTPBearer(auto_error=False)


def current_user(
    db: Db, credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]
):
    if credentials is None:
        raise HTTPException(
            401, "Se requiere autenticación", headers={"WWW-Authenticate": "Bearer"}
        )
    payload = Seguridad.decodificar_jwt(credentials.credentials)
    try:
        user = repo.get(db, UsuarioModel, int(payload["sub"]))
    except (ValueError, TypeError, KeyError):
        user = None
    if user is None or not user.activo:
        raise HTTPException(401, "Usuario inactivo o inexistente")
    if user.rol.nombre not in {
        "ADMIN_GENERAL",
        "GERENTE_SUCURSAL",
        "OPERADOR_INVENTARIO",
    }:
        raise HTTPException(403, "Rol sin permisos configurados")
    if user.rol.nombre != "ADMIN_GENERAL" and (
        user.sucursal is None or not user.sucursal.activa
    ):
        raise HTTPException(403, "El usuario requiere una sucursal activa")
    return user


User = Annotated[UsuarioModel, Depends(current_user)]


def admin(user: User):
    if user.rol.nombre != "ADMIN_GENERAL":
        raise HTTPException(403, "Se requiere rol ADMIN_GENERAL")
    return user


Admin = Annotated[UsuarioModel, Depends(admin)]


def branch_access(user, branch_id, manager=False):
    if user.rol.nombre != "ADMIN_GENERAL" and user.sucursal_id != branch_id:
        raise HTTPException(403, "No puedes operar sobre esta sucursal")
    if manager and user.rol.nombre not in {"ADMIN_GENERAL", "GERENTE_SUCURSAL"}:
        raise HTTPException(403, "Se requiere gerente o administrador")
