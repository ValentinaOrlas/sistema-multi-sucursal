from fastapi import APIRouter, Response
from controllers.transferencias.transferenciaControlador import TransferenciasControlador
from dtos.transferencias.TransferenciaDto import (
    TransferenciaCreateRequest, 
    PrepararEnvioRequest, 
    RecibirTransferenciaRequest
)

router = APIRouter(
    prefix="/api/transferencias",
    tags=["Módulo de Transferencias"]
)

@router.post("", status_code=201)
def solicitar_transferencia(datos: TransferenciaCreateRequest, response: Response):
    resultado, codigo_estado = TransferenciasControlador.solicitar_transferencia(datos.model_dump())
    response.status_code = codigo_estado
    return resultado

@router.post("/{transferencia_id}/enviar", status_code=200)
def preparar_y_enviar(transferencia_id: int, datos: PrepararEnvioRequest, response: Response):
    resultado, codigo_estado = TransferenciasControlador.preparar_y_enviar(transferencia_id, datos.model_dump())
    response.status_code = codigo_estado
    return resultado

@router.post("/{transferencia_id}/recibir", status_code=200)
def confirmar_recepcion(transferencia_id: int, datos: RecibirTransferenciaRequest, response: Response):
    resultado, codigo_estado = TransferenciasControlador.confirmar_recepcion(transferencia_id, datos.model_dump())
    response.status_code = codigo_estado
    return resultado

@router.get("/{transferencia_id}", status_code=200)
def obtener_detalle_transferencia(transferencia_id: int, response: Response):
    resultado, codigo_estado = TransferenciasControlador.obtener_transferencia(transferencia_id)
    response.status_code = codigo_estado
    return resultado