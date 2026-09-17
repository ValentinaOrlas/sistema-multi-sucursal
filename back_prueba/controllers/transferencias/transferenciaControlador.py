from service.transferencias.TransferenciaService import TransferenciasService

class TransferenciasControlador:

    @staticmethod
    def solicitar_transferencia(datos: dict) -> tuple:
        return TransferenciasService.solicitar_transferencia(datos)

    @staticmethod
    def preparar_y_enviar(transferencia_id: int, datos: dict) -> tuple:
        return TransferenciasService.preparar_y_enviar_transferencia(transferencia_id, datos)

    @staticmethod
    def confirmar_recepcion(transferencia_id: int, datos: dict) -> tuple:
        return TransferenciasService.confirmar_recepcion(transferencia_id, datos)

    @staticmethod
    def obtener_transferencia(transferencia_id: int) -> tuple:
        return TransferenciasService.obtener_transferencia(transferencia_id)