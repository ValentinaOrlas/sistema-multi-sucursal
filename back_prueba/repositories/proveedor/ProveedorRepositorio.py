from psycopg.rows import dict_row
from typing import Optional

class ProveedoresRepositorio:

    @staticmethod
    def crear_proveedor(cur, nombre: str, contacto: str, condiciones_comerciales: str, tiempo_entrega: int) -> int:
        cur.execute(
            """
            INSERT INTO proveedores (nombre, contacto, condiciones_comerciales, tiempo_entrega_promedio_dias)
            VALUES (%s, %s, %s, %s)
            RETURNING id;
            """,
            (nombre, contacto, condiciones_comerciales, tiempo_entrega)
        )
        return cur.fetchone()[0]

    @staticmethod
    def listar_proveedores(cur) -> list:
        cur.row_factory = dict_row
        cur.execute(
            """
            SELECT id, nombre, contacto, condiciones_comerciales, tiempo_entrega_promedio_dias 
            FROM proveedores 
            ORDER BY id ASC;
            """
        )
        return cur.fetchall()

    @staticmethod
    def obtener_por_id(cur, proveedor_id: int, incluir_productos=True) -> dict:
        cur.row_factory = dict_row
        cur.execute(
            """
            SELECT id, nombre, contacto, condiciones_comerciales, tiempo_entrega_promedio_dias 
            FROM proveedores 
            WHERE id = %s;
            """,
            (proveedor_id,)
        )
        proveedor = cur.fetchone()
        if not proveedor:
            return None

        if not incluir_productos:
            return proveedor

        # Obtener productos asociados
        cur.execute(
            """
            SELECT pp.id as relacion_id, p.id as producto_id, p.sku, p.nombre as producto_nombre, 
                   pp.precio_referencia, pp.activo
            FROM producto_proveedor pp
            JOIN productos p ON pp.producto_id = p.id
            WHERE pp.proveedor_id = %s;
            """,
            (proveedor_id,)
        )
        proveedor['productos_asociados'] = cur.fetchall()
        return proveedor

    @staticmethod
    def actualizar_proveedor(cur, proveedor_id: int, nombre: str, contacto: str, condiciones_comerciales: str, tiempo_entrega: int):
        cur.execute(
            """
            UPDATE proveedores 
            SET nombre = COALESCE(%s, nombre),
                contacto = COALESCE(%s, contacto),
                condiciones_comerciales = COALESCE(%s, condiciones_comerciales),
                tiempo_entrega_promedio_dias = COALESCE(%s, tiempo_entrega_promedio_dias)
            WHERE id = %s;
            """,
            (nombre, contacto, condiciones_comerciales, tiempo_entrega, proveedor_id)
        )

    @staticmethod
    def asociar_producto(cur, proveedor_id: int, producto_id: int, precio_referencia: float):
        cur.execute(
            """
            INSERT INTO producto_proveedor (proveedor_id, producto_id, precio_referencia, activo)
            VALUES (%s, %s, %s, TRUE)
            ON CONFLICT (proveedor_id, producto_id) 
            DO UPDATE SET precio_referencia = EXCLUDED.precio_referencia, activo = TRUE;
            """,
            (proveedor_id, producto_id, precio_referencia)
        )

    @staticmethod
    def evaluar_desempeno_entregas(cur, proveedor_id: int) -> list:
        cur.row_factory = dict_row
        # Compara el tiempo estimado registrado en el proveedor vs los días reales que tardaron las órdenes en recibirse
        cur.execute(
            """
            SELECT oc.id as orden_compra_id, oc.fecha_creacion, oc.fecha_recepcion,
                   p.tiempo_entrega_promedio_dias as tiempo_estimado_catalogo,
                   EXTRACT(EPOCH FROM (oc.fecha_recepcion - oc.fecha_creacion)) / 86400 as dias_reales_tardados
            FROM ordenes_compra oc
            JOIN proveedores p ON oc.proveedor_id = p.id
            WHERE oc.proveedor_id = %s AND oc.estado = 'RECIBIDA' AND oc.fecha_recepcion IS NOT NULL;
            """,
            (proveedor_id,)
        )
        return cur.fetchall()