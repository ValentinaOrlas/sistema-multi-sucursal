from typing import Optional
from service.reporte.ReporteService import ReportesService

class ReportesControlador:

    @staticmethod
    def generar_reporte(tipo: str, formato: str, fecha_inicio: str, fecha_fin: str, sucursal_id: Optional[int]) -> tuple:
        return ReportesService.generar_reporte(tipo, formato, fecha_inicio, fecha_fin, sucursal_id)