from psycopg.rows import dict_row
from typing import Optional

class DashboardRepositorio:

    @staticmethod
    def obtener_ventas_comparativa(cur, sucursal_id: int) -> dict:
        cur.row_factory = dict_row
        cur.execute(
            """
            SELECT 
                SUM(CASE WHEN fecha_venta >= DATE_TRUNC('month', CURRENT_TIMESTAMP) THEN total_venta ELSE 0 END) as ventas_mes_actual,
                SUM(CASE WHEN fecha_venta >= DATE_TRUNC('month', CURRENT_TIMESTAMP - INTERVAL '1 month') 
                          AND fecha_venta < DATE_TRUNC('month', CURRENT_TIMESTAMP) THEN total_venta ELSE 0 END) as ventas_mes_anterior
            FROM ventas
            WHERE sucursal_id = %s;
            """,
            (sucursal_id,)
        )
        return cur.fetchone() or {"ventas_mes_actual": 0.0, "ventas_mes_anterior": 0.0}

    @staticmethod
    def obtener_comportamiento_inventario(cur, sucursal_id: int) -> list:
        cur.row_factory = dict_row
        cur.execute(
            """
            SELECT 
                p.id as producto_id, p.nombre as producto_nombre, p.sku, p.unidad_medida,
                i.stock_actual, i.costo_promedio_ponderado,
                COALESCE(SUM(CASE WHEN v.fecha_venta >= DATE_TRUNC('month', CURRENT_TIMESTAMP) THEN dv.cantidad ELSE 0 END), 0) as unidades_vendidas_mes_actual
            FROM inventario_sucursal i
            JOIN productos p ON i.producto_id = p.id
            LEFT JOIN detalle_venta dv ON dv.producto_id = p.id
            LEFT JOIN ventas v ON dv.venta_id = v.id AND v.sucursal_id = i.sucursal_id
            WHERE i.sucursal_id = %s
            GROUP BY p.id, p.nombre, p.sku, p.unidad_medida, i.stock_actual, i.costo_promedio_ponderado
            ORDER BY unidades_vendidas_mes_actual DESC;
            """,
            (sucursal_id,)
        )
        return cur.fetchall()

    @staticmethod
    def obtener_transferencias_activas(cur, sucursal_id: int) -> list:
        cur.row_factory = dict_row
        cur.execute(
            """
            SELECT t.id as transferencia_id, t.estado, t.prioridad, t.created_at,
                   so.nombre as sucursal_origen, sd.nombre as sucursal_destino, t.transportista
            FROM transferencias t
            JOIN sucursales so ON t.sucursal_origen_id = so.id
            JOIN sucursales sd ON t.sucursal_destino_id = sd.id
            WHERE (t.sucursal_origen_id = %s OR t.sucursal_destino_id = %s)
              AND t.estado IN ('SOLICITADA', 'EN_PREPARACION', 'EN_TRANSITO')
            ORDER BY t.created_at DESC;
            """,
            (sucursal_id, sucursal_id)
        )
        return cur.fetchall()

    @staticmethod
    def obtener_alertas_reabastecimiento(cur, sucursal_id: int) -> list:
        cur.row_factory = dict_row
        cur.execute(
            """
            SELECT i.id, i.producto_id, p.nombre as producto_nombre, p.sku,
                   i.stock_actual, i.stock_minimo_local
            FROM inventario_sucursal i
            JOIN productos p ON i.producto_id = p.id
            WHERE i.sucursal_id = %s AND i.stock_actual <= i.stock_minimo_local
            ORDER BY i.stock_actual ASC;
            """,
            (sucursal_id,)
        )
        return cur.fetchall()

    @staticmethod
    def obtener_comparativa_sucursales(cur) -> list:
        cur.row_factory = dict_row
        cur.execute(
            """
            SELECT s.id as sucursal_id, s.nombre as sucursal_nombre, s.ubicacion,
                   COALESCE(SUM(CASE WHEN v.fecha_venta >= DATE_TRUNC('month', CURRENT_TIMESTAMP) THEN v.total_venta ELSE 0 END), 0) as total_ventas_mes_actual
            FROM sucursales s
            LEFT JOIN ventas v ON s.id = v.sucursal_id
            WHERE s.activa = TRUE
            GROUP BY s.id, s.nombre, s.ubicacion
            ORDER BY total_ventas_mes_actual DESC;
            """
        )
        return cur.fetchall()