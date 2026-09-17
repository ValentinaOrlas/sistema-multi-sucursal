from psycopg.rows import dict_row
from typing import Optional

class LogisticaRepositorio:

    @staticmethod
    def obtener_tiempos_transferencia(cur, transferencia_id: int) -> dict:
        cur.row_factory = dict_row
        cur.execute(
            """
            T.id as transferencia_id, t.estado, t.prioridad, t.created_at, 
            t.fecha_estimada_llegada, t.fecha_real_llegada,
            so.nombre as origen, sd.nombre as destino
            FROM transferencias t
            JOIN sucursales so ON t.sucursal_origen_id = so.id
            JOIN sucursales sd ON t.sucursal_destino_id = sd.id
            WHERE t.id = %s;
            """,
            (transferencia_id,)
        )
        return cur.fetchone()

    @staticmethod
    def listar_transferencias_en_curso(cur) -> list:
        cur.row_factory = dict_row
        cur.execute(
            """
            SELECT t.id as transferencia_id, t.estado, t.prioridad, t.created_at, 
                   t.fecha_estimada_llegada, so.nombre as sucursal_origen, 
                   sd.nombre as sucursal_destino, t.transportista
            FROM transferencias t
            JOIN sucursales so ON t.sucursal_origen_id = so.id
            JOIN sucursales sd ON t.sucursal_destino_id = sd.id
            WHERE t.estado IN ('SOLICITADA', 'EN_PREPARACION', 'EN_TRANSITO')
            ORDER BY t.created_at DESC;
            """
        )
        return cur.fetchall()

    @staticmethod
    def obtener_datos_para_reportes(cur, sucursal_id: Optional[int] = None) -> list:
        cur.row_factory = dict_row
        query = """
            SELECT t.id as transferencia_id, t.estado, t.prioridad, 
                   t.created_at, t.fecha_estimada_llegada, t.fecha_real_llegada,
                   so.id as origen_id, so.nombre as sucursal_origen,
                   sd.id as destino_id, sd.nombre as sucursal_destino,
                   COALESCE(SUM(dt.cantidad_enviada), 0) as total_unidades_enviadas
            FROM transferencias t
            JOIN sucursales so ON t.sucursal_origen_id = so.id
            JOIN sucursales sd ON t.sucursal_destino_id = sd.id
            LEFT JOIN detalle_transferencia dt ON t.id = dt.transferencia_id
            WHERE t.estado IN ('RECIBIDA_COMPLETA', 'RECIBIDA_PARCIAL')
        """
        params = []
        if sucursal_id:
            query += " AND (t.sucursal_origen_id = %s OR t.sucursal_destino_id = %s)"
            params.extend([sucursal_id, sucursal_id])

        query += " GROUP BY t.id, so.id, so.nombre, sd.id, sd.nombre ORDER BY t.created_at DESC;"
        cur.execute(query, params)
        return cur.fetchall()