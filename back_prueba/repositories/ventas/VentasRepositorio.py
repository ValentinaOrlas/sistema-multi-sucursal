from repositories.gestion_inventario.InventarioRepositorio import InventarioRepositorio as R

class VentasRepositorio:
    @staticmethod
    def crear_venta(cur, sucursal_id, usuario_id, total):
        return R.fila(cur, '''INSERT INTO ventas(sucursal_id,usuario_id,total_venta,fecha_venta)
            VALUES(%s,%s,%s,CURRENT_TIMESTAMP AT TIME ZONE 'UTC') RETURNING id''', (sucursal_id,usuario_id,total))['id']

    @staticmethod
    def detalle(cur, venta_id, item):
        cur.execute('''INSERT INTO detalle_venta(venta_id,producto_id,cantidad,precio_unitario,descuento_aplicado)
            VALUES(%s,%s,%s,%s,%s)''', (venta_id,item['producto_id'],item['cantidad'],item['precio_unitario'],item['descuento_aplicado']))

    @staticmethod
    def obtener_comprobante_por_id(cur, venta_id):
        venta = R.fila(cur, '''SELECT v.*,v.id AS venta_id,u.nombre AS responsable_nombre,s.nombre AS sucursal_nombre
            FROM ventas v JOIN usuarios u ON u.id=v.usuario_id JOIN sucursales s ON s.id=v.sucursal_id
            WHERE v.id=%s''', (venta_id,))
        if venta:
            venta['detalles'] = R.filas(cur, '''SELECT d.*,p.sku,p.nombre AS producto_nombre,p.unidad_medida
                FROM detalle_venta d JOIN productos p ON p.id=d.producto_id WHERE d.venta_id=%s ORDER BY d.id''', (venta_id,))
        return venta

    @staticmethod
    def listar(cur, sucursal_id):
        ventas = R.filas(cur, '''SELECT v.*,u.nombre AS responsable_nombre FROM ventas v
            JOIN usuarios u ON u.id=v.usuario_id WHERE (%s::int IS NULL OR v.sucursal_id=%s)
            ORDER BY v.fecha_venta DESC,v.id DESC''', (sucursal_id,sucursal_id))
        if ventas:
            detalles = R.filas(cur, 'SELECT * FROM detalle_venta WHERE venta_id=ANY(%s) ORDER BY id', ([v['id'] for v in ventas],))
            grupos = {v['id']: [] for v in ventas}
            for d in detalles:
                grupos[d['venta_id']].append(d)
            for v in ventas:
                v['detalles'] = grupos[v['id']]
        return ventas

    @staticmethod
    def listas(cur):
        return R.filas(cur, 'SELECT * FROM listas_precios ORDER BY nombre,id')

    @staticmethod
    def precios(cur, lista_id):
        return R.filas(cur, 'SELECT * FROM precios_producto WHERE lista_id=%s ORDER BY producto_id', (lista_id,))
