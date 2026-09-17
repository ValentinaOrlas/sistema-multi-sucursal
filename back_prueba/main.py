from dotenv import load_dotenv
load_dotenv()
import uvicorn
from fastapi import FastAPI, Request, Depends
import logging
from psycopg import IntegrityError
from segurity.dependencias import obtener_usuario_actual
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from routers.gestion_inventario.inventarioRouter import router as inventarioRouter
from routers.compras.compraRouter import router as compraRouter
from routers.ventas.routerVentas import router as ventaRouter
from routers.transferencias.transferenciaRouter import router as transferenciaRouter
from routers.tiemposLogistica.tiempoRouter import router as tiempoRouter
from routers.dashboard.dashboardRouter import router as dashboarRouter
from routers.proveedor.proveedorRouter import router as proveedorRouter
from routers.reporte.reporteRouter import router as reporteRouter
from routers.login.authRouter import router as authRouter

app = FastAPI(
    title="API Gestion Inventario",
    description="Sistema de gestión de inventario",
    version="1.0.0"
)

# Carpeta para archivos estáticos (imágenes subidas)
UPLOAD_DIR = "static"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Montar archivos estáticos para que el frontend pueda visualizar las imágenes
app.mount("/static", StaticFiles(directory=UPLOAD_DIR), name="static")

# Capturador global de errores no controlados (evita caída de CORS en error 500)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.getLogger(__name__).error("Error procesando petición", exc_info=exc)
    return JSONResponse(status_code=500, content={"mensaje": "Error interno del servidor."})

@app.exception_handler(IntegrityError)
async def integrity_error(request: Request, exc: IntegrityError):
    mensajes = {
        '23505': 'Ya existe un registro con ese SKU o nombre.',
        '23503': 'El registro no existe o tiene inventario/historial asociado. No se puede completar la operación.',
        '23514': 'Los datos no cumplen las restricciones de la base de datos.',
    }
    return JSONResponse(status_code=409, content={'detail': mensajes.get(exc.sqlstate, 'Los datos no cumplen las restricciones de la base de datos.')})

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # O simplemente allow_origins=["*"] para evitar bloqueos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rutas
app.include_router(inventarioRouter)
app.include_router(compraRouter)
app.include_router(ventaRouter)
app.include_router(transferenciaRouter, dependencies=[Depends(obtener_usuario_actual)])
app.include_router(tiempoRouter, dependencies=[Depends(obtener_usuario_actual)])
app.include_router(dashboarRouter, dependencies=[Depends(obtener_usuario_actual)])
app.include_router(proveedorRouter)
app.include_router(reporteRouter, dependencies=[Depends(obtener_usuario_actual)])
app.include_router(authRouter)

@app.get("/")
def home():
    return {"mensaje": "API de inventario multisucursal funcionando correctamente"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)