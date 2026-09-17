from fastapi import APIRouter, Depends
from controllers.ventas.ventasControlador import VentasControlador as C
from dtos.ventas.VentasDto import VentaCreateRequest
from segurity.dependencias import obtener_usuario_actual, admin_o_gerente

# DEPENDENICA GLOBAL DEL ROUTER: 
# Acceso base para cualquier usuario logueado (Operadores necesitan cobrar y ver listas de precios).
router = APIRouter(
    prefix='/api', 
    tags=['Ventas'], 
    dependencies=[Depends(obtener_usuario_actual)]
)

# --- OPERACIÓN DE CAJA / ALMACÉN (Acceso: Cualquier rol - Operadores, Gerentes, Admins) ---

@router.post('/ventas', status_code=201)
def registrar(datos: VentaCreateRequest, usuario=Depends(obtener_usuario_actual)):
    # El operador registra la salida de mercancía por venta
    return C.registrar_venta(datos.model_dump(), usuario)

@router.get('/ventas/{venta_id}')
def obtener(venta_id: int, usuario=Depends(obtener_usuario_actual)):
    # El operador puede necesitar consultar o reimprimir el comprobante de una venta específica
    return C.obtener_comprobante(venta_id, usuario)

@router.get('/listas-precios')
def listas():
    # El sistema (caja) necesita consultar esto al momento de armar la venta
    return C.listas()

@router.get('/listas-precios/{lista_id}/precios')
def precios(lista_id: int):
    # El sistema (caja) necesita consultar los precios exactos para aplicarlos a la venta
    return C.precios(lista_id)


# --- REPORTES Y SUPERVISIÓN (Acceso: Exclusivo Administrador o Gerente) ---

@router.get('/ventas')
def listar(sucursal_id: int | None = None, usuario=Depends(admin_o_gerente)):   
    return C.listar(usuario, sucursal_id)