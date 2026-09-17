from fastapi import APIRouter, Depends
from controllers.ventas.ventasControlador import VentasControlador as C
from dtos.ventas.VentasDto import VentaCreateRequest
from segurity.dependencias import obtener_usuario_actual

router = APIRouter(prefix='/api', tags=['Ventas'], dependencies=[Depends(obtener_usuario_actual)])

@router.post('/ventas', status_code=201)
def registrar(datos: VentaCreateRequest, usuario=Depends(obtener_usuario_actual)):
    return C.registrar_venta(datos.model_dump(), usuario)

@router.get('/ventas')
def listar(sucursal_id: int | None = None, usuario=Depends(obtener_usuario_actual)):
    return C.listar(usuario, sucursal_id)

@router.get('/ventas/{venta_id}')
def obtener(venta_id: int, usuario=Depends(obtener_usuario_actual)):
    return C.obtener_comprobante(venta_id, usuario)

@router.get('/listas-precios')
def listas():
    return C.listas()

@router.get('/listas-precios/{lista_id}/precios')
def precios(lista_id: int):
    return C.precios(lista_id)
