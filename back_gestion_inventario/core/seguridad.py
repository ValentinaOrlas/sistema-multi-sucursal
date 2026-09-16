import os
from datetime import datetime, timedelta, timezone
import bcrypt
import jwt
from fastapi import HTTPException


def secret():
    value = os.getenv("SECRET_KEY", "")
    if len(value) < 32:
        raise RuntimeError("Configura SECRET_KEY con al menos 32 caracteres")
    return value


class Seguridad:
    @staticmethod
    def encriptarContrasena(contrasena: str) -> str:
        if len(contrasena.encode()) > 72:
            raise HTTPException(
                422, "La contraseña debe tener como máximo 72 bytes UTF-8"
            )
        return bcrypt.hashpw(contrasena.encode(), bcrypt.gensalt()).decode()

    @staticmethod
    def verificar_contrasena(contrasena_plana: str, contrasena_encriptada: str) -> bool:
        try:
            return bcrypt.checkpw(
                contrasena_plana.encode(), contrasena_encriptada.encode()
            )
        except (ValueError, TypeError):
            return False

    @staticmethod
    def generar_jwt(payload: dict) -> str:
        now = datetime.now(timezone.utc)
        return jwt.encode(
            {
                **payload,
                "iat": now,
                "exp": now + timedelta(hours=int(os.getenv("EXPIRATION_HOURS", "8"))),
            },
            secret(),
            algorithm="HS256",
        )

    @staticmethod
    def decodificar_jwt(token: str) -> dict:
        try:
            return jwt.decode(
                token,
                secret(),
                algorithms=["HS256"],
                options={"require": ["sub", "exp", "iat"]},
            )
        except jwt.PyJWTError:
            raise HTTPException(
                401, "Token inválido o expirado", headers={"WWW-Authenticate": "Bearer"}
            )
