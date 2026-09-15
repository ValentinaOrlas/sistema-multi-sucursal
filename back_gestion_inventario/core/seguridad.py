# core/security.py
import os
import bcrypt
import datetime
import jwt
from fastapi import HTTPException, status

SECRET_KEY = os.getenv("SECRET_KEY", "tu_clave_secreta_super_segura")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
EXPIRATION_HOURS = int(os.getenv("EXPIRATION_HOURS", 8))

class Seguridad:

    @staticmethod
    def encriptarContrasena(contrasena: str) -> str:
        contrasena_bytes = contrasena.encode('utf-8')[:72]
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(contrasena_bytes, salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verificar_contrasena(contrasena_plana: str, contrasena_encriptada: str) -> bool:
        contrasena_bytes = contrasena_plana.encode('utf-8')[:72]
        hash_bytes = contrasena_encriptada.encode('utf-8')
        return bcrypt.checkpw(contrasena_bytes, hash_bytes)

    @staticmethod
    def generar_jwt(payload: dict) -> str:
        datos = payload.copy()
        expiracion = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=EXPIRATION_HOURS)
        datos.update({"exp": expiracion})
        
        token = jwt.encode(datos, SECRET_KEY, algorithm=ALGORITHM)
        return token

    @staticmethod
    def decodificar_jwt(token: str) -> dict:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="El token de sesión ha expirado.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de autenticación inválido.",
                headers={"WWW-Authenticate": "Bearer"},
            )