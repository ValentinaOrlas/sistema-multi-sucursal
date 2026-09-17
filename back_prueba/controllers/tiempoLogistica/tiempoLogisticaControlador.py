from service.tiemposLogistica.TiempoLogisticaService import LogisticaService

class LogisticaControlador:

    @staticmethod
    def consultar_tiempos(transferencia_id: int) -> tuple:
        return LogisticaService.consultar_tiempos(transferencia_id)

    @staticmethod
    def listar_en_curso() -> tuple:
        return LogisticaService.listar_en_curso()

    @staticmethod
    def generar_reporte(sucursal_id: int = None, clasificar_por: str = None) -> tuple:
        return LogisticaService.generar_reporte_cumplimiento(sucursal_id, clasificar_por)