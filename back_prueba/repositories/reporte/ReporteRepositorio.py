from psycopg.rows import dict_row
from typing import Optional

class ReportesRepositorio:

    @staticmethod
    def obtener_datos_ventas(cur, fecha_inicio: str, fecha_fin: str, sucursal_id: Optional[int]) -> list:
        cur.row_factory = dict_row
        query = """
            SELECT v.id, v.fecha_venta, s.nombre as sucursal, u.nombre as vendedor, v.total_venta
            FROM ventas v
            JOIN sucursales s ON v.sucursal_id = s.id
            JOIN usuarios u ON v.usuario_id = u.id
            WHERE v.fecha_venta >= %s AND v.fecha_venta <= %s
        """
        params = [fecha_inicio, fecha_fin]
        if sucursal_id:
            query += " AND v.sucursal_id = %s"
            params.append(sucursal_id)
        
        query += " ORDER BY v.fecha_venta DESC;"
        cur.execute(query, params)
        return cur.fetchall()

    @staticmethod
    def obtener_datos_movimientos(cur, fecha_inicio: str, fecha_fin: str, sucursal_id: Optional[int]) -> list:
        cur.row_factory = dict_row
        query = """
            SELECT m.id, m.fecha_movimiento, s.nombre as sucursal, p.nombre as producto, 
                   m.tipo_movimiento, m.cantidad, m.motivo
            FROM movimientos_inventario m
            JOIN sucursales s ON m.sucursal_id = s.id
            JOIN productos p ON m.producto_id = p.id
            WHERE m.fecha_movimiento >= %s AND m.fecha_movimiento <= %s
        """
        params = [fecha_inicio, fecha_fin]
        if sucursal_id:
            query += " AND m.sucursal_id = %s"
            params.append(sucursal_id)
        
        query += " ORDER BY m.fecha_movimiento DESC;"
        cur.execute(query, params)
        return cur.fetchall()

    @staticmethod
    def obtener_datos_transferencias(cur, fecha_inicio: str, fecha_fin: str, sucursal_id: Optional[int]) -> list:
        cur.row_factory = dict_row
        query = """
            SELECT t.id, t.created_at as fecha, t.estado, t.prioridad, 
                   so.nombre as origen, sd.nombre as destino
            FROM transferencias t
            JOIN sucursales so ON t.sucursal_origen_id = so.id
            JOIN sucursales sd ON t.sucursal_destino_id = sd.id
            WHERE t.created_at >= %s AND t.created_at <= %s
        """
        params = [fecha_inicio, fecha_fin]
        if sucursal_id:
            query += " AND (t.sucursal_origen_id = %s OR t.sucursal_destino_id = %s)"
            params.append(sucursal_id)
        
        query += " ORDER BY t.created_at DESC;"
        cur.execute(query, params)
        return cur.fetchall()