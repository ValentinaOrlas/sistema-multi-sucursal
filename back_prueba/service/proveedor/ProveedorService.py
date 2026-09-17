from typing import Optional
from repositories.proveedor.ProveedorRepositorio import ProveedoresRepositorio
from conection.conectionDb import con_cursor

class ProveedoresService:

    @staticmethod
    @con_cursor
    def crear_proveedor(cur, datos: dict) -> tuple:
        try:
            proveedor_id = ProveedoresRepositorio.crear_proveedor(
                cur,
                nombre=datos['nombre'],
                contacto=datos.get('contacto'),
                condiciones_comerciales=datos.get('condiciones_comerciales'),
                tiempo_entrega=datos['tiempo_entrega_promedio_dias']
            )
            return {"mensaje": "Proveedor creado exitosamente", "proveedor_id": proveedor_id}, 201
        except Exception as e:
            return {"error": str(e)}, 400

    @staticmethod
    @con_cursor
    def listar_proveedores(cur) -> tuple:
        proveedores = ProveedoresRepositorio.listar_proveedores(cur)
        return {"proveedores": proveedores}, 200

    @staticmethod
    @con_cursor
    def obtener_proveedor_detalle(cur, proveedor_id: int) -> tuple:
        proveedor = ProveedoresRepositorio.obtener_por_id(cur, proveedor_id)
        if not proveedor:
            return {"error": "Proveedor no encontrado"}, 404
        return proveedor, 200

    @staticmethod
    @con_cursor
    def actualizar_proveedor(cur, proveedor_id: int, datos: dict) -> tuple:
        existente = ProveedoresRepositorio.obtener_por_id(cur, proveedor_id, incluir_productos=False)
        if not existente:
            return {"error": "Proveedor no encontrado"}, 404

        try:
            ProveedoresRepositorio.actualizar_proveedor(
                cur,
                proveedor_id=proveedor_id,
                nombre=datos.get('nombre'),
                contacto=datos.get('contacto'),
                condiciones_comerciales=datos.get('condiciones_comerciales'),
                tiempo_entrega=datos.get('tiempo_entrega_promedio_dias')
            )
            return {"mensaje": "Proveedor actualizado exitosamente"}, 200
        except Exception as e:
            return {"error": str(e)}, 400

    @staticmethod
    @con_cursor
    def asociar_producto_proveedor(cur, proveedor_id: int, datos: dict) -> tuple:
        existente = ProveedoresRepositorio.obtener_por_id(cur, proveedor_id, incluir_productos=False)
        if not existente:
            return {"error": "Proveedor no encontrado"}, 404

        try:
            ProveedoresRepositorio.asociar_producto(
                cur,
                proveedor_id=proveedor_id,
                producto_id=datos['producto_id'],
                precio_referencia=datos.get('precio_referencia')
            )
            return {"mensaje": "Producto asociado al proveedor exitosamente"}, 200
        except Exception as e:
            return {"error": str(e)}, 400

    @staticmethod
    @con_cursor
    def evaluar_tiempos_entrega(cur, proveedor_id: int) -> tuple:
        existente = ProveedoresRepositorio.obtener_por_id(cur, proveedor_id, incluir_productos=False)
        if not existente:
            return {"error": "Proveedor no encontrado"}, 404

        historial = ProveedoresRepositorio.evaluar_desempeno_entregas(cur, proveedor_id)
        
        evaluaciones = []
        total_dias_reales = 0.0
        cantidad_ordenes = len(historial)

        for h in historial:
            dias_reales = round(float(h['dias_reales_tardados']), 2)
            total_dias_reales += dias_reales
            estimado = h['tiempo_estimado_catalogo']
            
            estado_cumplimiento = "A tiempo" if dias_reales <= estimado else "Fuera de plazo"
            
            evaluaciones.append({
                "orden_compra_id": h['orden_compra_id'],
                "fecha_creacion": h['fecha_creacion'],
                "fecha_recepcion": h['fecha_recepcion'],
                "tiempo_estimado_dias": estimado,
                "tiempo_real_dias": dias_reales,
                "evaluacion": estado_cumplimiento
            })

        promedio_real = round(total_dias_reales / cantidad_ordenes, 2) if cantidad_ordenes > 0 else 0.0

        resumen = {
            "proveedor_id": proveedor_id,
            "nombre": existente['nombre'],
            "tiempo_promedio_registrado_catalogo": existente['tiempo_entrega_promedio_dias'],
            "tiempo_promedio_real_calculado": promedio_real,
            "total_ordenes_evaluadas": cantidad_ordenes,
            "detalle_ordenes": evaluaciones
        }

        return resumen, 200