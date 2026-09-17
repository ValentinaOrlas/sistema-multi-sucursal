from decimal import Decimal, ROUND_HALF_UP
from fastapi import HTTPException
from conection.conectionDb import con_cursor
from repositories.ventas.VentasRepositorio import VentasRepositorio as R
from service.gestion_inventario.InventarioService import sucursal_activa, filtro_sucursal, alcance, mover_stock

class VentasService:
    @staticmethod
    @con_cursor
    def registrar_venta(cur, datos, usuario):
        sucursal_activa(cur, usuario, datos['sucursal_id'])
        detalles = datos['detalles']
        if len({d['producto_id'] for d in detalles}) != len(detalles):
            raise HTTPException(422, 'Incluye cada producto una sola vez.')
        precios = {p['producto_id']: p['precio'] for p in R.precios(cur, datos['lista_precio_id'])} if datos.get('lista_precio_id') else None
        total = Decimal(0)
        for d in detalles:
            precio = precios.get(d['producto_id']) if precios is not None else d['precio_unitario']
            if precio is None:
                raise HTTPException(422, 'Falta el precio de uno de los productos.')
            d['precio_unitario'] = precio
            total += (d['cantidad'] * precio * (1-d['descuento_aplicado']/100)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        venta_id = R.crear_venta(cur, datos['sucursal_id'], usuario['id'], total)
        # Orden estable para evitar bloqueos cruzados entre ventas concurrentes.
        for d in sorted(detalles, key=lambda d: d['producto_id']):
            mover_stock(cur, dict(sucursal_id=datos['sucursal_id'],producto_id=d['producto_id'],
                cantidad=d['cantidad'],tipo_movimiento='RETIRO',motivo='VENTA'), usuario['id'], venta_id=venta_id)
            R.detalle(cur, venta_id, d)
        return {'mensaje': 'Venta registrada.', 'comprobante': R.obtener_comprobante_por_id(cur, venta_id)}

    @staticmethod
    @con_cursor
    def obtener_comprobante(cur, venta_id, usuario):
        venta = R.obtener_comprobante_por_id(cur, venta_id)
        if not venta:
            raise HTTPException(404, 'Venta no encontrada.')
        alcance(usuario, venta['sucursal_id'])
        return venta

    @staticmethod
    @con_cursor
    def listar(cur, usuario, sucursal_id=None):
        return R.listar(cur, filtro_sucursal(usuario, sucursal_id))

    @staticmethod
    @con_cursor
    def listas(cur):
        return R.listas(cur)

    @staticmethod
    @con_cursor
    def precios(cur, lista_id):
        if not any(l['id'] == lista_id for l in R.listas(cur)):
            raise HTTPException(404, 'Lista de precios no encontrada.')
        return R.precios(cur, lista_id)
