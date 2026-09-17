import os
import jwt
import bcrypt
import hmac
from datetime import datetime, timedelta
from repositories.login.LoginRepositorio import AuthRepositorio
from conection.conectionDb import con_cursor

class AuthService:

    @staticmethod
    @con_cursor
    def login(cur, datos: dict) -> tuple:
        email = datos['email']
        password_ingresada = datos['password']

        # 1. Buscar usuario
        usuario = AuthRepositorio.obtener_usuario_por_email(cur, email)
        if not usuario:
            return {"error": "Credenciales inválidas"}, 401

        # Acepta los hashes existentes sin reemplazar contraseñas.
        guardada = usuario['password_hash']
        try:
            valida = (bcrypt.checkpw(password_ingresada.encode(), guardada.encode())
                      if guardada.startswith(('$2a$', '$2b$', '$2y$'))
                      else hmac.compare_digest(guardada.encode(), password_ingresada.encode()))
        except ValueError:
            valida = False
        if not valida:
            return {"error": "Credenciales inválidas"}, 401

        # 3. Generar el Token JWT
        secret_key = os.getenv("JWT_SECRET_KEY")
        algorithm = os.getenv("JWT_ALGORITHM")
        expire_minutes = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 120))

        fecha_expiracion = datetime.utcnow() + timedelta(minutes=expire_minutes)

        # La información que viaja dentro del token (Payload)
        payload = {
            "sub": str(usuario['id']),
            "email": usuario['email'],
            "rol": usuario['rol'],
            "sucursal_id": usuario['sucursal_id'],
            "exp": fecha_expiracion
        }

        token = jwt.encode(payload, secret_key, algorithm=algorithm)

        return {
            "mensaje": "Login exitoso",
            "access_token": token,
            "token_type": "bearer",
            "usuario": {
                "id": usuario['id'],
                "nombre": usuario['nombre'],
                "rol": usuario['rol'],
                "sucursal_id": usuario['sucursal_id']
            }
        }, 200

    @staticmethod
    @con_cursor
    def usuario_actual(cur, usuario_id):
        return AuthRepositorio.obtener_usuario_por_id(cur, usuario_id)
