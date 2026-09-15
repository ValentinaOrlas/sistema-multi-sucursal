from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

# Conexión a BD y carga de modelos
from conection.conectionDb import engine
import models  

# Creación automática de las tablas en PostgreSQL en caso de que no existan
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API Sistema Multi-Sucursal",
    description="Sistema de gestión de inventario",
    version="1.0.0"
)

# Evita caída de CORS en error 500
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"mensaje": f"Error interno del servidor: {str(exc)}"},
    )

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"mensaje": "API funcionando correctamente"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)