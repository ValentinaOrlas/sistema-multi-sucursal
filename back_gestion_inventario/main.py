from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(
    title="API Sistema Multi-Sucursal",
    description="Sistema de gestión de inventario",
    version="1.0.0"
)



#evita caída de CORS en error 500
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"mensaje": f"Error interno del servidor: {str(exc)}"},
    )
    

@app.get("/")
def home():
    return {"mensaje": "API funcionando correctamente"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)