from fastapi import HTTPException
from conection.conectionDb import con_cursor
from repositories.compras.CompraRepositorio import ComprasRepositorio as R
from service.gestion_inventario.InventarioService import sucursal_activa, filtro_sucursal, alcance, exigir_rol, mover_stock

class ComprasService:
    @staticmethod
    @con_cursor
    def crear(cur, datos, usuario):
        sucursal_activa(cur, usuario, datos['sucursal_destino_id'])
        if len({d['producto_id'] for d in datos['detalles']}) != len(datos['detalles']):
            raise HTTPException(422, 'Incluye cada producto una sola vez.')
        orden = R.crear_orden(cur, datos, usuario['id'])
        return {'id': orden['id'], 'orden_compra_id': orden['id'], 'mensaje': 'Orden creada.'}

    @staticmethod
    @con_cursor
    def listar(cur, usuario, sucursal_id=None, proveedor_id=None, producto_id=None):
        return R.listar(cur, filtro_sucursal(usuario,sucursal_id), proveedor_id, producto_id)

    @staticmethod
    @con_cursor
    def obtener(cur, orden_id, usuario):
        orden = R.obtener_orden_por_id(cur, orden_id)
        if not orden:
            raise HTTPException(404, 'Orden no encontrada.')
        alcance(usuario, orden['sucursal_destino_id'])
        return orden

    @staticmethod
    @con_cursor
    def recibir(cur, orden_id, usuario):
        orden = R.obtener_orden_por_id(cur, orden_id, bloquear=True)
        if not orden:
            raise HTTPException(404, 'Orden no encontrada.')
        sucursal_activa(cur, usuario, orden['sucursal_destino_id'])
        if orden['estado'] != 'PENDIENTE':
            raise HTTPException(409, 'Solo se pueden recibir órdenes pendientes.')
        for item in orden['detalles']:
            mover_stock(cur, dict(sucursal_id=orden['sucursal_destino_id'],producto_id=item['producto_id'],
                cantidad=item['cantidad'],costo_unitario=item['precio_unitario']*(1-item['descuento']/100),
                tipo_movimiento='INGRESO',motivo='COMPRA'), usuario['id'], orden_id=orden_id)
        R.estado(cur, orden_id, 'RECIBIDA')
        return {'mensaje': 'Compra recibida; stock y trazabilidad actualizados.'}

    @staticmethod
    @con_cursor
    def cancelar(cur, orden_id, usuario):
        exigir_rol(usuario, 'ADMIN_GENERAL', 'GERENTE_SUCURSAL')
        orden = R.obtener_orden_por_id(cur, orden_id, bloquear=True)
        if not orden:
            raise HTTPException(404, 'Orden no encontrada.')
        sucursal_activa(cur, usuario, orden['sucursal_destino_id'])
        if orden['estado'] != 'PENDIENTE':
            raise HTTPException(409, 'Solo se pueden cancelar órdenes pendientes.')
        R.estado(cur, orden_id, 'CANCELADA')
        return {'mensaje': 'Orden cancelada.'}
