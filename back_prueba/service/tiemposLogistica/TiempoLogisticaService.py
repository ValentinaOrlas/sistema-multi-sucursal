from typing import Optional
from repositories.tiemposLogistica.TiempoLogisticaRepositorio import LogisticaRepositorio
from conection.conectionDb import con_cursor

class LogisticaService:

    @staticmethod
    @con_cursor
    def consultar_tiempos(cur, transferencia_id: int) -> tuple:
        transf = LogisticaRepositorio.obtener_tiempos_transferencia(cur, transferencia_id)
        if not transf:
            return {"error": "Transferencia no encontrada"}, 404

        # Cálculo lógico de cumplimiento de tiempos
        creacion = transf['created_at']
        estimada = transf['fecha_estimada_llegada']
        real = transf['fecha_real_llegada']

        retraso_horas = None
        if real and estimada:
            diferencia = real - estimada
            retraso_horas = round(diferencia.total_seconds() / 3600, 2)

        resultado = {
            **transf,
            "retraso_horas": retraso_horas,
            "estado_tiempo": "A tiempo" if (retraso_horas is not None and retraso_horas <= 0) else "Con retraso/Fuera de plazo"
        }
        return resultado, 200

    @staticmethod
    @con_cursor
    def listar_en_curso(cur) -> tuple:
        transferencias = LogisticaRepositorio.listar_transferencias_en_curso(cur)
        return {"transferencias_en_curso": transferencias}, 200

    @staticmethod
    @con_cursor
    def generar_reporte_cumplimiento(cur, sucursal_id: Optional[int], clasificar_por: Optional[str]) -> tuple:
        registros = LogisticaRepositorio.obtener_datos_para_reportes(cur, sucursal_id)
        reporte_procesado = []

        for reg in registros:
            # 1. Cálculo del Costo Logístico Estimado (Lógico)
            # Factor base según prioridad + costo por volumen de unidades enviadas
            factor_prioridad = {"ALTA": 50.0, "MEDIA": 30.0, "BAJA": 15.0}.get(reg['prioridad'], 20.0)
            unidades = reg['total_unidades_enviadas']
            costo_transporte_estimado = factor_prioridad + (unidades * 1.5) # Tarifa lógica por unidad

            # 2. Cálculo del Tiempo Real de Entrega en Horas
            duracion_real_horas = None
            if reg['fecha_real_llegada'] and reg['created_at']:
                duracion_real_horas = round((reg['fecha_real_llegada'] - reg['created_at']).total_seconds() / 3600, 2)

            reporte_procesado.append({
                "transferencia_id": reg['transferencia_id'],
                "ruta": f"{reg['sucursal_origen']} ➔ {reg['sucursal_destino']}",
                "prioridad": reg['prioridad'],
                "estado": reg['estado'],
                "duracion_real_horas": duracion_real_horas,
                "costo_logistico_estimado": round(costo_transporte_estimado, 2)
            })

        # 3. Clasificación lógica según solicitud
        if clasificar_por == "costo":
            reporte_procesado.sort(key=lambda x: x['costo_logistico_estimado'], reverse=True)
        elif clasificar_por == "tiempo":
            reporte_procesado.sort(key=lambda x: x['duracion_real_horas'] if x['duracion_real_horas'] is not None else 0)
        elif clasificar_por == "prioridad":
            orden_prioridad = {"ALTA": 1, "MEDIA": 2, "BAJA": 3}
            reporte_procesado.sort(key=lambda x: orden_prioridad.get(x['prioridad'], 4))

        return {"total_registros": len(reporte_procesado), "clasificacion": clasificar_por or "ninguna", "reporte": reporte_procesado}, 200