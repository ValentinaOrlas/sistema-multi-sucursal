import logging
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, DataError
from core.dependencies import Db
from routes import (
    auth_routes as auth,
    catalogos_routes as catalogos,
    inventario_routes as inventario,
    operaciones_routes as operaciones,
    reportes_routes as reportes,
)
from routes.producto_routes import (
    router as registro_producto_router,
)
from middlewares.autenticacion_middleware import (
    RegistroProductoMiddleware,
)
from exceptions.producto_exceptions import (
    ErrorRegistroProducto,
)
from exceptions.handlers import manejar_error_registro

app = FastAPI(
    title="API Sistema Multi-Sucursal",
    version="1.0.0",
    description="Inventario, compras, ventas y transferencias. Cantidades en unidad base; descuentos porcentuales. Fechas almacenadas en UTC.",
)
app.add_middleware(RegistroProductoMiddleware)
app.add_exception_handler(ErrorRegistroProducto, manejar_error_registro)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.exception_handler(IntegrityError)
def integrity_error(request: Request, exc: IntegrityError):
    return JSONResponse(
        status_code=409,
        content={
            "detail": "La operación viola una relación, un valor único o una restricción de datos"
        },
    )


@app.exception_handler(DataError)
def data_error(request: Request, exc: DataError):
    return JSONResponse(
        status_code=422, content={"detail": "Valor fuera del rango admitido"}
    )


@app.exception_handler(Exception)
def unexpected_error(request: Request, exc: Exception):
    logging.getLogger(__name__).exception(
        "Error procesando %s", request.url.path, exc_info=exc
    )
    return JSONResponse(
        status_code=500, content={"detail": "Error interno del servidor"}
    )


@app.get("/")
def home():
    return {"mensaje": "API Sistema Multi-Sucursal", "documentacion": "/docs"}


@app.get("/health")
def health(db: Db):
    db.execute(text("SELECT 1"))
    return {"status": "ok"}


for router in (
    registro_producto_router,
    auth.router,
    catalogos.router,
    inventario.router,
    operaciones.router,
    reportes.router,
):
    app.include_router(router, prefix="/api")
