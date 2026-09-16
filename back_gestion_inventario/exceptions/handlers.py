"""Traduce los errores del caso de uso a respuestas HTTP."""

from fastapi import Request
from fastapi.responses import JSONResponse
from .producto_exceptions import (
    ErrorRegistroProducto,
    SkuDuplicado,
    CategoriaNoEncontrada,
    UsuarioNoAutenticado,
    OperadorRequerido,
    SucursalNoDisponible,
)

ESTADOS = {
    SkuDuplicado: 409,
    CategoriaNoEncontrada: 404,
    UsuarioNoAutenticado: 401,
    OperadorRequerido: 403,
    SucursalNoDisponible: 403,
}


def manejar_error_registro(request: Request, exc: ErrorRegistroProducto):
    estado = ESTADOS.get(type(exc), 400)
    return JSONResponse(
        status_code=estado,
        content={"codigo": exc.codigo, "detail": str(exc)},
        headers={"WWW-Authenticate": "Bearer"} if estado == 401 else None,
    )
