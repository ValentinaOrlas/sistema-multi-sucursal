"""Interceptor de autenticación para la creación de productos."""

from fastapi import HTTPException
from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send
from core.seguridad import Seguridad


class RegistroProductoMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        path = (
            scope.get("path", "").removeprefix(scope.get("root_path", "")).rstrip("/")
        )
        if (
            scope["type"] != "http"
            or scope.get("method") != "POST"
            or path != "/api/productos"
        ):
            await self.app(scope, receive, send)
            return
        authorization = Headers(scope=scope).get("authorization", "")
        scheme, _, token = authorization.partition(" ")
        try:
            if scheme.lower() != "bearer" or not token.strip():
                raise ValueError("Token ausente")
            payload = Seguridad.decodificar_jwt(token.strip())
            usuario_id = int(payload["sub"])
            if usuario_id <= 0:
                raise ValueError("Identificador inválido")
        except (HTTPException, ValueError, TypeError, KeyError):
            response = JSONResponse(
                status_code=401,
                content={
                    "codigo": "AUTENTICACION_REQUERIDA",
                    "detail": "Se requiere un token Bearer válido y vigente.",
                },
                headers={"WWW-Authenticate": "Bearer"},
            )
            await response(scope, receive, send)
            return
        # Estado interno, nunca obtenido del cuerpo ni de cabeceras de usuario.
        # El servicio comprueba la vigencia del usuario y su permiso.
        scope.setdefault("state", {})["registro_producto_usuario_id"] = usuario_id
        await self.app(scope, receive, send)
