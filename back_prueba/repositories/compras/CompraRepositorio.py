from repositories.gestion_inventario.InventarioRepositorio import InventarioRepositorio as R

class ComprasRepositorio:
    @staticmethod
    def crear_orden(cur, d, usuario_id):
        orden = R.fila(cur, '''INSERT INTO ordenes_compra(proveedor_id,sucursal_destino_id,usuario_id,estado,plazo_pago_dias,fecha_creacion)
            VALUES(%s,%s,%s,'PENDIENTE',%s,CURRENT_TIMESTAMP AT TIME ZONE 'UTC') RETURNING *''',
            (d['proveedor_id'],d['sucursal_destino_id'],usuario_id,d['plazo_pago_dias']))
        for item in d['detalles']:
            cur.execute('''INSERT INTO detalle_orden_compra(orden_compra_id,producto_id,cantidad,precio_unitario,descuento)
                VALUES(%s,%s,%s,%s,%s)''', (orden['id'],item['producto_id'],item['cantidad'],item['precio_unitario'],item['descuento']))
        return orden

    @staticmethod
    def obtener_orden_por_id(cur, orden_id, bloquear=False):
        orden = R.fila(cur, 'SELECT * FROM ordenes_compra WHERE id=%s' + (' FOR UPDATE' if bloquear else ''), (orden_id,))
        if orden:
            orden['detalles'] = R.filas(cur, '''SELECT d.*,p.nombre AS producto_nombre,p.sku FROM detalle_orden_compra d
                JOIN productos p ON p.id=d.producto_id WHERE orden_compra_id=%s ORDER BY d.producto_id''', (orden_id,))
        return orden

    @staticmethod
    def listar(cur, sucursal_id=None, proveedor_id=None, producto_id=None):
        ordenes = R.filas(cur, '''SELECT o.* FROM ordenes_compra o
            WHERE (%s::int IS NULL OR o.sucursal_destino_id=%s) AND (%s::int IS NULL OR o.proveedor_id=%s)
            AND (%s::int IS NULL OR EXISTS(SELECT 1 FROM detalle_orden_compra d WHERE d.orden_compra_id=o.id AND d.producto_id=%s))
            ORDER BY o.fecha_creacion DESC,o.id DESC''', (sucursal_id,sucursal_id,proveedor_id,proveedor_id,producto_id,producto_id))
        if ordenes:
            detalles = R.filas(cur, 'SELECT * FROM detalle_orden_compra WHERE orden_compra_id=ANY(%s) ORDER BY id', ([o['id'] for o in ordenes],))
            grupos = {o['id']: [] for o in ordenes}
            for d in detalles:
                grupos[d['orden_compra_id']].append(d)
            for o in ordenes:
                o['detalles'] = grupos[o['id']]
        return ordenes

    @staticmethod
    def estado(cur, orden_id, estado):
        cur.execute('''UPDATE ordenes_compra SET estado=%s,
            fecha_recepcion=CASE WHEN %s='RECIBIDA' THEN CURRENT_TIMESTAMP AT TIME ZONE 'UTC' ELSE fecha_recepcion END
            WHERE id=%s''', (estado,estado,orden_id))
