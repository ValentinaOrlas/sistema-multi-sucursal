import os
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from service.login.LoginService import AuthService

security = HTTPBearer(auto_error=False)

def obtener_usuario_actual(credentials: HTTPAuthorizationCredentials | None = Depends(security)):
    if not credentials:
        raise HTTPException(401, 'Inicia sesión para continuar.')
    try:
        payload = jwt.decode(credentials.credentials, os.environ['JWT_SECRET_KEY'],
            algorithms=[os.getenv('JWT_ALGORITHM', 'HS256')], options={'require': ['sub', 'exp']})
        usuario_id = int(payload['sub'])
    except (jwt.InvalidTokenError, ValueError, TypeError, KeyError):
        raise HTTPException(401, 'Sesión inválida o expirada.')
    usuario = AuthService.usuario_actual(usuario_id)
    if not usuario:
        raise HTTPException(401, 'El usuario no está activo.')
    return {**usuario, 'sub': str(usuario['id'])}

def solo_admin(usuario=Depends(obtener_usuario_actual)):
    if usuario['rol'] != 'ADMIN_GENERAL':
        raise HTTPException(403, 'Se requiere rol de administrador.')
    return usuario

def admin_o_gerente(usuario=Depends(obtener_usuario_actual)):
    if usuario['rol'] not in ('ADMIN_GENERAL', 'GERENTE_SUCURSAL'):
        raise HTTPException(403, 'Se requiere rol administrativo.')
    return usuario

cualquier_usuario_autenticado = obtener_usuario_actual
