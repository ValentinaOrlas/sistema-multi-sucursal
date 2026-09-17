from typing import Optional
from repositories.dashboard.DashboardRepositorio import DashboardRepositorio
from conection.conectionDb import con_cursor

class DashboardService:

    @staticmethod
    @con_cursor
    def obtener_dashboard_sucursal(cur, sucursal_id: int) -> tuple:
        # 1. Volumen de ventas mes actual vs anterior
        ventas_raw = DashboardRepositorio.obtener_ventas_comparativa(cur, sucursal_id)
        actual = float(ventas_raw['ventas_mes_actual'] or 0)
        anterior = float(ventas_raw['ventas_mes_anterior'] or 0)
        
        crecimiento_porcentaje = 0.0
        if anterior > 0:
            crecimiento_porcentaje = round(((actual - anterior) / anterior) * 100, 2)

        ventas_resumen = {
            "ventas_mes_actual": actual,
            "ventas_mes_anterior": anterior,
            "crecimiento_porcentaje": crecimiento_porcentaje
        }

        # 2. Comportamiento del inventario, rotación y clasificación de demanda
        inventario_raw = DashboardRepositorio.obtener_comportamiento_inventario(cur, sucursal_id)
        productos_analisis = []
        
        for item in inventario_raw:
            stock = item['stock_actual']
            salidas = item['unidades_vendidas_mes_actual']
            
            # Cálculo de rotación lógica (salidas / stock actual o base segura)
            rotacion_indice = round(salidas / stock, 2) if stock > 0 else float(salidas)

            # Clasificación lógica de demanda
            if salidas >= 10:  # Umbral dinámico configurable
                demanda = "ALTA"
            elif salidas > 0:
                demanda = "MEDIA"
            else:
                demanda = "BAJA (Estancado)"

            productos_analisis.append({
                "producto_id": item['producto_id'],
                "sku": item['sku'],
                "nombre": item['producto_nombre'],
                "stock_actual": stock,
                "unidades_vendidas_mes": salidas,
                "indice_rotacion": rotacion_indice,
                "clasificacion_demanda": demanda
            })

        # 3. Estado de transferencias activas
        transferencias_activas = DashboardRepositorio.obtener_transferencias_activas(cur, sucursal_id)

        # 4. Indicadores de reabastecimiento (próximos a agotarse o bajo mínimo)
        alertas_reabastecimiento = DashboardRepositorio.obtener_alertas_reabastecimiento(cur, sucursal_id)

        dashboard_data = {
            "sucursal_id": sucursal_id,
            "ventas": ventas_resumen,
            "inventario_analisis": productos_analisis,
            "transferencias_activas": transferencias_activas,
            "alertas_reabastecimiento": alertas_reabastecimiento
        }

        return dashboard_data, 200

    @staticmethod
    @con_cursor
    def obtener_dashboard_administrativo(cur) -> tuple:
        # Comparativa de rendimiento global entre sucursales (para perfiles administrativos)
        comparativa = DashboardRepositorio.obtener_comparativa_sucursales(cur)
        return {"comparativa_sucursales": comparativa}, 200