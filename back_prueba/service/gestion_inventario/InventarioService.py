from decimal import Decimal
from fastapi import HTTPException
from conection.conectionDb import con_cursor
from repositories.gestion_inventario.InventarioRepositorio import InventarioRepositorio as R


def exigir_rol(usuario, *roles):
    if usuario['rol'] not in roles:
        raise HTTPException(403, 'Tu rol no permite realizar esta operación.')


def alcance(usuario, sucursal_id):
    if usuario['rol'] != 'ADMIN_GENERAL' and (not sucursal_id or sucursal_id != usuario['sucursal_id']):
        raise HTTPException(403, 'La operación corresponde a otra sucursal.')


def sucursal_activa(cur, usuario, sucursal_id):
    alcance(usuario, sucursal_id)
    sucursal = R.sucursal(cur, sucursal_id)
    if not sucursal:
        raise HTTPException(404, 'Sucursal no encontrada.')
    if not sucursal['activa']:
        raise HTTPException(409, 'La sucursal está inactiva.')


def filtro_sucursal(usuario, sucursal_id):
    if usuario['rol'] == 'ADMIN_GENERAL':
        return sucursal_id
    sucursal_id = sucursal_id or usuario['sucursal_id']
    alcance(usuario, sucursal_id)
    return sucursal_id


def mover_stock(cur, datos, usuario_id, venta_id=None, orden_id=None):
    """El stock y su historial se guardan en la misma transacción del servicio."""
    inv = R.bloquear_inventario(cur, datos['sucursal_id'], datos['producto_id'])
    cantidad = Decimal(datos['cantidad'])
    if datos['tipo_movimiento'] == 'INGRESO':
        costo = Decimal(datos['costo_unitario']).quantize(Decimal('0.000001'))
        stock = inv['stock_actual'] + cantidad
        promedio = ((inv['stock_actual'] * inv['costo_promedio_ponderado'] + cantidad * costo) / stock).quantize(Decimal('0.000001'))
    else:
        if inv['stock_actual'] < cantidad:
            raise HTTPException(409, 'Stock insuficiente para completar la operación.')
        stock = inv['stock_actual'] - cantidad
        costo = promedio = inv['costo_promedio_ponderado']
    R.guardar_stock(cur, inv['id'], stock, promedio)
    return R.movimiento(cur, datos, stock, usuario_id, costo, venta_id, orden_id)


class InventarioService:
    @staticmethod
    @con_cursor
    def productos(cur, categoria_id=None):
        return R.productos(cur, categoria_id)

    @staticmethod
    @con_cursor
    def producto(cur, producto_id):
        producto = R.producto(cur, producto_id)
        if not producto:
            raise HTTPException(404, 'Producto no encontrado.')
        return producto

    @staticmethod
    @con_cursor
    def crear(cur, datos, usuario):
        exigir_rol(usuario, 'OPERADOR_INVENTARIO')
        sucursal_activa(cur, usuario, usuario['sucursal_id'])
        producto = R.crear_producto(cur, datos)
        inv = R.bloquear_inventario(cur, usuario['sucursal_id'], producto['id'])
        R.minimo(cur, inv['id'], datos['stock_minimo'])
        mover_stock(cur, dict(sucursal_id=usuario['sucursal_id'],producto_id=producto['id'],
            cantidad=datos['cantidad_inicial'],costo_unitario=datos['costo_unitario'],
            tipo_movimiento='INGRESO',motivo='Registro inicial de producto'), usuario['id'])
        return producto

    @staticmethod
    @con_cursor
    def actualizar(cur, producto_id, datos, usuario):
        exigir_rol(usuario, 'ADMIN_GENERAL', 'GERENTE_SUCURSAL', 'OPERADOR_INVENTARIO')
        producto = R.actualizar_producto(cur, producto_id, datos)
        if not producto:
            raise HTTPException(404, 'Producto no encontrado.')
        return producto

    @staticmethod
    @con_cursor
    def eliminar(cur, producto_id, usuario):
        exigir_rol(usuario, 'ADMIN_GENERAL')
        if not R.eliminar_producto(cur, producto_id):
            raise HTTPException(404, 'Producto no encontrado.')
        return {'mensaje': 'Producto eliminado.'}

    @staticmethod
    @con_cursor
    def categorias(cur):
        return R.categorias(cur)

    @staticmethod
    @con_cursor
    def crear_categoria(cur, datos, usuario):
        exigir_rol(usuario, 'ADMIN_GENERAL')
        return R.crear_categoria(cur, datos)

    @staticmethod
    @con_cursor
    def sucursales(cur):
        return R.sucursales(cur)

    @staticmethod
    @con_cursor
    def inventario(cur, sucursal_id=None):
        return R.inventarios(cur, sucursal_id)

    @staticmethod
    @con_cursor
    def minimo(cur, datos, usuario):
        exigir_rol(usuario, 'ADMIN_GENERAL', 'GERENTE_SUCURSAL')
        sucursal_activa(cur, usuario, datos['sucursal_id'])
        inv = R.bloquear_inventario(cur, datos['sucursal_id'], datos['producto_id'])
        return R.minimo(cur, inv['id'], datos['stock_minimo_local'])

    @staticmethod
    @con_cursor
    def registrar(cur, datos, usuario):
        exigir_rol(usuario, 'OPERADOR_INVENTARIO')
        sucursal_activa(cur, usuario, datos['sucursal_id'])
        if datos['tipo_movimiento'] not in ('INGRESO', 'RETIRO'):
            raise HTTPException(422, 'Indica INGRESO o RETIRO.')
        if datos['tipo_movimiento'] == 'INGRESO' and datos.get('costo_unitario') is None:
            raise HTTPException(422, 'El costo unitario es obligatorio para los ingresos.')
        return mover_stock(cur, datos, usuario['id'])

    @staticmethod
    @con_cursor
    def movimientos(cur, usuario, sucursal_id=None, producto_id=None, fecha_inicio=None, fecha_fin=None):
        sucursal_id = filtro_sucursal(usuario, sucursal_id)
        if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
            raise HTTPException(422, 'El rango de fechas es inválido.')
        return R.movimientos(cur, sucursal_id, producto_id, fecha_inicio, fecha_fin)


    @staticmethod
    @con_cursor
    def alertas(cur, sucursal_id):
        return [i for i in R.inventarios(cur, sucursal_id) if i['stock_actual'] <= i['stock_minimo_local']]
