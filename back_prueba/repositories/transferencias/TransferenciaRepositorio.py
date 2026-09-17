from psycopg.rows import dict_row

class TransferenciasRepositorio:

    @staticmethod
    def crear_transferencia(cur, sucursal_origen_id: int, sucursal_destino_id: int, usuario_id: int, prioridad: str) -> int:
        cur.execute(
            """
            INSERT INTO transferencias (sucursal_origen_id, sucursal_destino_id, usuario_solicitante_id, estado, prioridad)
            VALUES (%s, %s, %s, 'SOLICITADA', %s)
            RETURNING id;
            """,
            (sucursal_origen_id, sucursal_destino_id, usuario_id, prioridad)
        )
        return cur.fetchone()[0]

    @staticmethod
    def crear_detalle_transferencia(cur, transferencia_id: int, producto_id: int, cantidad_solicitada: int):
        cur.execute(
            """
            INSERT INTO detalle_transferencia (transferencia_id, producto_id, cantidad, cantidad_solicitada, cantidad_enviada, cantidad_recibida, faltantes)
            VALUES (%s, %s, %s, %s, 0, 0, 0);
            """,
            (transferencia_id, producto_id, cantidad_solicitada, cantidad_solicitada)
        )

    @staticmethod
    def obtener_transferencia_por_id(cur, transferencia_id: int) -> dict:
        cur.row_factory = dict_row
        cur.execute(
            """
            SELECT t.*, 
                   so.nombre as sucursal_origen_nombre, 
                   sd.nombre as sucursal_destino_nombre,
                   u.nombre as usuario_nombre
            FROM transferencias t
            JOIN sucursales so ON t.sucursal_origen_id = so.id
            JOIN sucursales sd ON t.sucursal_destino_id = sd.id
            JOIN usuarios u ON t.usuario_solicitante_id = u.id
            WHERE t.id = %s;
            """,
            (transferencia_id,)
        )
        transf = cur.fetchone()
        if not transf:
            return None

        cur.execute(
            """
            SELECT dt.*, p.nombre as producto_nombre, p.sku, p.unidad_medida
            FROM detalle_transferencia dt
            JOIN productos p ON dt.producto_id = p.id
            WHERE dt.transferencia_id = %s;
            """,
            (transferencia_id,)
        )
        transf['detalles'] = cur.fetchall()
        return transf

    @staticmethod
    def actualizar_a_en_preparacion(cur, transferencia_id: int):
        cur.execute(
            """
            UPDATE transferencias SET estado = 'EN_PREPARACION' WHERE id = %s;
            """,
            (transferencia_id,)
        )

    @staticmethod
    def registrar_envio(cur, transferencia_id: int, transportista: str, fecha_estimada: str):
        cur.execute(
            """
            UPDATE transferencias 
            SET estado = 'EN_TRANSITO', transportista = %s, fecha_estimada_llegada = %s 
            WHERE id = %s;
            """,
            (transportista, fecha_estimada, transferencia_id)
        )

    @staticmethod
    def actualizar_detalle_envio(cur, transferencia_id: int, producto_id: int, cantidad_enviada: int):
        cur.execute(
            """
            UPDATE detalle_transferencia 
            SET cantidad_enviada = %s, cantidad = %s 
            WHERE transferencia_id = %s AND producto_id = %s;
            """,
            (cantidad_enviada, cantidad_enviada, transferencia_id, producto_id)
        )

    @staticmethod
    def obtener_inventario(cur, sucursal_id: int, producto_id: int) -> dict:
        cur.row_factory = dict_row
        cur.execute(
            """
            SELECT id, stock_actual, costo_promedio_ponderado 
            FROM inventario_sucursal 
            WHERE sucursal_id = %s AND producto_id = %s;
            """,
            (sucursal_id, producto_id)
        )
        return cur.fetchone()

    @staticmethod
    def actualizar_stock_inventario(cur, sucursal_id: int, producto_id: int, nuevo_stock: int):
        cur.execute(
            """
            UPDATE inventario_sucursal 
            SET stock_actual = %s 
            WHERE sucursal_id = %s AND producto_id = %s;
            """,
            (nuevo_stock, sucursal_id, producto_id)
        )

    @staticmethod
    def insertar_inventario_destino(cur, sucursal_id: int, producto_id: int, stock_inicial: int, cpp_inicial: float):
        cur.execute(
            """
            INSERT INTO inventario_sucursal (sucursal_id, producto_id, stock_actual, stock_minimo_local, costo_promedio_ponderado)
            VALUES (%s, %s, %s, 5, %s);
            """,
            (sucursal_id, producto_id, stock_inicial, cpp_inicial)
        )

    @staticmethod
    def registrar_movimiento(cur, sucursal_id: int, producto_id: int, cantidad: int, tipo: str, stock_resultante: int):
        cur.execute(
            """
            INSERT INTO movimientos_inventario (sucursal_id, producto_id, cantidad, tipo_movimiento, motivo, stock_resultante)
            VALUES (%s, %s, %s, %s, 'TRANSFERENCIA', %s);
            """,
            (sucursal_id, producto_id, cantidad, tipo, stock_resultante)
        )

    @staticmethod
    def actualizar_detalle_recepcion(cur, transferencia_id: int, producto_id: int, cantidad_recibida: int, faltantes: int, tratamiento: str):
        cur.execute(
            """
            UPDATE detalle_transferencia 
            SET cantidad_recibida = %s, faltantes = %s, tratamiento_faltante = %s 
            WHERE transferencia_id = %s AND producto_id = %s;
            """,
            (cantidad_recibida, faltantes, tratamiento if tratamiento != "None" else None, transferencia_id, producto_id)
        )

    @staticmethod
    def finalizar_transferencia(cur, transferencia_id: int, estado_final: str):
        cur.execute(
            """
            UPDATE transferencias 
            SET estado = %s, fecha_real_llegada = CURRENT_TIMESTAMP 
            WHERE id = %s;
            """,
            (estado_final, transferencia_id)
        )