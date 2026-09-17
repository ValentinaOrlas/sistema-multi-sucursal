from fastapi import APIRouter, Response, Depends
from controllers.login.loginControlador import AuthControlador
from dtos.login.LoginDto import LoginRequest

router = APIRouter(
    prefix="/api/auth",
    tags=["Autenticación"]
)

@router.post("/login", status_code=200)
def iniciar_sesion(datos: LoginRequest, response: Response):
    resultado, codigo_estado = AuthControlador.login(datos.model_dump())
    response.status_code = codigo_estado
    return resultado

from segurity.dependencias import obtener_usuario_actual

@router.get('/me')
def perfil(usuario=Depends(obtener_usuario_actual)):
    return {**usuario, 'rol': {'nombre': usuario['rol']}}
