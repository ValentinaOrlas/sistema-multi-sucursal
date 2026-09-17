from datetime import date
from fastapi import APIRouter, Depends
from controllers.gestion_inventario.inventarioControlador import InventarioControlador as C
from dtos.gestion_inventario.inventarioDto import ProductoCreateRequest, ProductoUpdateRequest, MovimientoRequest, MinimoRequest, CategoriaRequest
from segurity.dependencias import obtener_usuario_actual

router = APIRouter(prefix='/api', tags=['Inventario y Productos'], dependencies=[Depends(obtener_usuario_actual)])

@router.get('/inventario/productos')
@router.get('/productos', include_in_schema=False)
def productos(categoria_id: int | None = None):
    return C.productos(categoria_id)

@router.post('/inventario/productos', status_code=201)
@router.post('/productos', status_code=201, include_in_schema=False)
def crear(datos: ProductoCreateRequest, usuario=Depends(obtener_usuario_actual)):
    return C.crear(datos.model_dump(), usuario)

@router.get('/inventario/productos/{producto_id}')
@router.get('/productos/{producto_id}', include_in_schema=False)
def producto(producto_id: int):
    return C.producto(producto_id)

@router.patch('/inventario/productos/{producto_id}')
@router.patch('/productos/{producto_id}', include_in_schema=False)
def actualizar(producto_id: int, datos: ProductoUpdateRequest, usuario=Depends(obtener_usuario_actual)):
    return C.actualizar(producto_id, datos.model_dump(), usuario)

@router.delete('/inventario/productos/{producto_id}')
@router.delete('/productos/{producto_id}', include_in_schema=False)
def eliminar(producto_id: int, usuario=Depends(obtener_usuario_actual)):
    return C.eliminar(producto_id, usuario)

@router.get('/categorias')
def categorias():
    return C.categorias()

@router.post('/categorias', status_code=201)
def crear_categoria(datos: CategoriaRequest, usuario=Depends(obtener_usuario_actual)):
    return C.crear_categoria(datos.model_dump(), usuario)

@router.get('/sucursales')
def sucursales():
    return C.sucursales()

@router.get('/inventario')
def inventario(sucursal_id: int | None = None):
    return C.inventario(sucursal_id)

@router.get('/inventario/sucursales/{sucursal_id}')
def inventario_sucursal(sucursal_id: int):
    return C.inventario(sucursal_id)

@router.get('/inventario/sucursales/{sucursal_id}/alertas')
def alertas(sucursal_id: int):
    return C.alertas(sucursal_id)

@router.post('/inventario')
def minimo(datos: MinimoRequest, usuario=Depends(obtener_usuario_actual)):
    return C.minimo(datos.model_dump(), usuario)

@router.get('/inventario/movimientos')
def movimientos(sucursal_id: int | None = None, producto_id: int | None = None,
                fecha_inicio: date | None = None, fecha_fin: date | None = None,
                usuario=Depends(obtener_usuario_actual)):
    return C.movimientos(usuario, sucursal_id, producto_id, fecha_inicio, fecha_fin)

@router.post('/inventario/movimientos', status_code=201)
def registrar(datos: MovimientoRequest, usuario=Depends(obtener_usuario_actual)):
    return C.registrar(datos.model_dump(), usuario)

@router.post('/inventario/movimientos/ingreso', status_code=201)
def ingreso(datos: MovimientoRequest, usuario=Depends(obtener_usuario_actual)):
    return C.registrar({**datos.model_dump(), 'tipo_movimiento': 'INGRESO'}, usuario)

@router.post('/inventario/movimientos/retiro', status_code=201)
def retiro(datos: MovimientoRequest, usuario=Depends(obtener_usuario_actual)):
    return C.registrar({**datos.model_dump(), 'tipo_movimiento': 'RETIRO'}, usuario)
