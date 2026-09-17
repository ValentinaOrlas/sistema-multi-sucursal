from fastapi import APIRouter, Depends
from controllers.compras.compraControlador import ComprasControlador as C
from dtos.compras.compraDto import OrdenCompraCreateRequest
from segurity.dependencias import obtener_usuario_actual, admin_o_gerente

router = APIRouter(prefix='/api/compras', tags=['Compras'], dependencies=[Depends(obtener_usuario_actual)])

# --- GESTIÓN DE ÓRDENES DE COMPRA Y CONDICIONES (Acceso: Administrador o Gerente) ---

@router.post('/ordenes', status_code=201)
@router.post('', status_code=201, include_in_schema=False)
def crear(datos: OrdenCompraCreateRequest, usuario=Depends(admin_o_gerente)):
    # Crear órdenes implica negociar precios unitarios, descuentos y plazos de pago
    return C.crear(datos.model_dump(), usuario)

@router.post('/ordenes/{orden_id}/cancelar')
@router.post('/{orden_id}/cancelar', include_in_schema=False)
def cancelar(orden_id: int, usuario=Depends(admin_o_gerente)):
    # Cancelar una orden de compra compromete presupuesto y proveedores
    return C.cancelar(orden_id, usuario)


# --- HISTÓRICO Y CONSULTAS (Acceso: Administrador o Gerente) ---

@router.get('/ordenes')
@router.get('/historico')
@router.get('', include_in_schema=False)
def listar(sucursal_id: int | None = None, proveedor_id: int | None = None,
           producto_id: int | None = None, usuario=Depends(admin_o_gerente)):
    # El histórico incluye costos, proveedores y análisis financiero por producto
    return C.listar(usuario, sucursal_id, proveedor_id, producto_id)

@router.get('/ordenes/{orden_id}')
@router.get('/{orden_id}', include_in_schema=False)
def obtener(orden_id: int, usuario=Depends(admin_o_gerente)):
    return C.obtener(orden_id, usuario)


# --- RECEPCIÓN DE MERCANCÍA E INVENTARIO (Acceso: Operadores, Gerentes y Admins) ---

@router.post('/ordenes/{orden_id}/recibir')
@router.post('/{orden_id}/recibir', include_in_schema=False)
def recibir(orden_id: int, usuario=Depends(obtener_usuario_actual)):
    # Confirmar la recepción actualiza automáticamente el inventario y calcula el costo promedio ponderado.
    # Puede hacerlo un operador en muelle/almacén o el gerente de sucursal.
    return C.recibir(orden_id, usuario)