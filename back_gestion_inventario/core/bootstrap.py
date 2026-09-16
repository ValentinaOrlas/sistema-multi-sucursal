"""Carga roles y, si se configuró, el primer administrador sin sobrescribir usuarios."""

import os
from sqlalchemy import select
from conection.conectionDb import SessionLocal
from core.seguridad import Seguridad, secret
from models import RoleModel, UsuarioModel
from models.inserciones import insertar_roles


def bootstrap():
    secret()
    with SessionLocal.begin() as db:
        insertar_roles(db)
        email, password = os.getenv("ADMIN_EMAIL"), os.getenv("ADMIN_PASSWORD")
        if email and password:
            if len(password) < 10:
                raise ValueError("ADMIN_PASSWORD requiere al menos 10 caracteres")
            if (
                db.scalar(
                    select(UsuarioModel).where(UsuarioModel.email == email.lower())
                )
                is None
            ):
                role = db.scalar(
                    select(RoleModel).where(RoleModel.nombre == "ADMIN_GENERAL")
                )
                db.add(
                    UsuarioModel(
                        nombre="Administrador",
                        email=email.lower(),
                        password_hash=Seguridad.encriptarContrasena(password),
                        rol_id=role.id,
                    )
                )


if __name__ == "__main__":
    bootstrap()
