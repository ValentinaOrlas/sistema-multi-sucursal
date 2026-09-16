import bcrypt
from core.seguridad import Seguridad
from dtos.schemas import Login
from fastapi import HTTPException
from models import UsuarioModel
from repositories import inventario_repository as repo

DUMMY_HASH = bcrypt.hashpw(b"non-user-password", bcrypt.gensalt()).decode()


def login(payload: Login, db):
    user = repo.find(db, UsuarioModel, email=str(payload.email).lower())
    valid = Seguridad.verificar_contrasena(
        payload.password, user.password_hash if user else DUMMY_HASH
    )
    if not valid or user is None or not user.activo:
        raise HTTPException(
            401, "Credenciales inválidas", headers={"WWW-Authenticate": "Bearer"}
        )
    return {
        "access_token": Seguridad.generar_jwt({"sub": str(user.id)}),
        "token_type": "bearer",
    }


def me(user):
    return user
