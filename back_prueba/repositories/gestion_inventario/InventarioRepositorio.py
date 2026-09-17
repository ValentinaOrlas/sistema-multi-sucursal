from psycopg.rows import dict_row

class InventarioRepositorio:
    @staticmethod
    def filas(cur, sql, params=()):
        cur.row_factory = dict_row
        cur.execute(sql, params)
        return cur.fetchall()

    @staticmethod
    def fila(cur, sql, params=()):
        cur.row_factory = dict_row
        cur.execute(sql, params)
        return cur.fetchone()

    @staticmethod
    def productos(cur, categoria_id=None):
        return InventarioRepositorio.filas(cur, '''SELECT p.*, c.nombre AS categoria
            FROM productos p JOIN categorias c ON c.id=p.categoria_id
            WHERE (%s::int IS NULL OR p.categoria_id=%s) ORDER BY p.nombre, p.id''', (categoria_id, categoria_id))

    @staticmethod
    def producto(cur, producto_id):
        return InventarioRepositorio.fila(cur, 'SELECT * FROM productos WHERE id=%s', (producto_id,))

    @staticmethod
    def crear_producto(cur, d):
        return InventarioRepositorio.fila(cur, '''INSERT INTO productos
            (sku,nombre,descripcion,categoria_id,unidad_medida,stock_minimo_global)
            VALUES (%s,%s,%s,%s,%s,0) RETURNING *''',
            (d['sku'],d['nombre'],d['descripcion'],d['categoria_id'],d['unidad_medida']))

    @staticmethod
    def actualizar_producto(cur, producto_id, d):
        return InventarioRepositorio.fila(cur, '''UPDATE productos SET sku=%s,nombre=%s,
            descripcion=%s,categoria_id=%s WHERE id=%s RETURNING *''',
            (d['sku'],d['nombre'],d['descripcion'],d['categoria_id'],producto_id))

    @staticmethod
    def eliminar_producto(cur, producto_id):
        return InventarioRepositorio.fila(cur, 'DELETE FROM productos WHERE id=%s RETURNING id', (producto_id,))

    @staticmethod
    def categorias(cur):
        return InventarioRepositorio.filas(cur, 'SELECT * FROM categorias ORDER BY nombre,id')

    @staticmethod
    def crear_categoria(cur, d):
        return InventarioRepositorio.fila(cur, 'INSERT INTO categorias(nombre,descripcion) VALUES(%s,%s) RETURNING *', (d['nombre'],d['descripcion']))

    @staticmethod
    def sucursales(cur):
        return InventarioRepositorio.filas(cur, 'SELECT * FROM sucursales ORDER BY nombre,id')

    @staticmethod
    def sucursal(cur, sucursal_id):
        return InventarioRepositorio.fila(cur, 'SELECT * FROM sucursales WHERE id=%s', (sucursal_id,))

    @staticmethod
    def inventarios(cur, sucursal_id=None):
        return InventarioRepositorio.filas(cur, '''SELECT i.*, p.sku,p.nombre FROM inventario_sucursal i
            JOIN productos p ON p.id=i.producto_id WHERE (%s::int IS NULL OR i.sucursal_id=%s)
            ORDER BY i.sucursal_id,p.nombre,i.id''', (sucursal_id,sucursal_id))

    @staticmethod
    def bloquear_inventario(cur, sucursal_id, producto_id):
        cur.execute('''INSERT INTO inventario_sucursal(sucursal_id,producto_id,stock_actual,stock_minimo_local,costo_promedio_ponderado)
            VALUES(%s,%s,0,0,0) ON CONFLICT(sucursal_id,producto_id) DO NOTHING''', (sucursal_id,producto_id))
        return InventarioRepositorio.fila(cur, '''SELECT * FROM inventario_sucursal
            WHERE sucursal_id=%s AND producto_id=%s FOR UPDATE''', (sucursal_id,producto_id))

    @staticmethod
    def guardar_stock(cur, inventario_id, cantidad, costo):
        cur.execute('UPDATE inventario_sucursal SET stock_actual=%s,costo_promedio_ponderado=%s WHERE id=%s', (cantidad,costo,inventario_id))

    @staticmethod
    def minimo(cur, inventario_id, minimo):
        return InventarioRepositorio.fila(cur, 'UPDATE inventario_sucursal SET stock_minimo_local=%s WHERE id=%s RETURNING *', (minimo,inventario_id))

    @staticmethod
    def movimiento(cur, d, stock, usuario_id, costo, venta_id=None, orden_id=None):
        return InventarioRepositorio.fila(cur, '''INSERT INTO movimientos_inventario
            (sucursal_id,producto_id,cantidad,tipo_movimiento,motivo,stock_resultante,usuario_id,costo_unitario,venta_id,orden_compra_id,fecha_movimiento)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,CURRENT_TIMESTAMP AT TIME ZONE 'UTC') RETURNING *''',
            (d['sucursal_id'],d['producto_id'],d['cantidad'],d['tipo_movimiento'],d['motivo'],stock,usuario_id,costo,venta_id,orden_id))

    @staticmethod
    def movimientos(cur, sucursal_id=None, producto_id=None, fecha_inicio=None, fecha_fin=None):
        return InventarioRepositorio.filas(cur, '''SELECT m.*,u.nombre AS responsable_nombre,
            p.sku,p.nombre AS producto,s.nombre AS sucursal FROM movimientos_inventario m
            LEFT JOIN usuarios u ON u.id=m.usuario_id JOIN productos p ON p.id=m.producto_id
            JOIN sucursales s ON s.id=m.sucursal_id
            WHERE (%s::int IS NULL OR m.sucursal_id=%s) AND (%s::int IS NULL OR m.producto_id=%s)
            AND (%s::date IS NULL OR m.fecha_movimiento >= %s::date)
            AND (%s::date IS NULL OR m.fecha_movimiento < %s::date + INTERVAL '1 day')
            ORDER BY m.fecha_movimiento DESC,m.id DESC''',
            (sucursal_id,sucursal_id,producto_id,producto_id,fecha_inicio,fecha_inicio,fecha_fin,fecha_fin))
