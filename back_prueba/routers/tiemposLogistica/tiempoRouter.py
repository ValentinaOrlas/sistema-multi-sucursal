from fastapi import APIRouter, Response, Query
from typing import Optional
from controllers.tiempoLogistica.tiempoLogisticaControlador import LogisticaControlador

router = APIRouter(
    prefix="/api/logistica",
    tags=["Módulo de Tiempos de Envío y Logística"]
)

@router.get("/transferencias/{transferencia_id}/tiempos", status_code=200)
def consultar_tiempos_transferencia(transferencia_id: int, response: Response):
    resultado, codigo_estado = LogisticaControlador.consultar_tiempos(transferencia_id)
    response.status_code = codigo_estado
    return resultado

@router.get("/transferencias/en-curso", status_code=200)
def visualizar_transferencias_en_curso(response: Response):
    resultado, codigo_estado = LogisticaControlador.listar_en_curso()
    response.status_code = codigo_estado
    return resultado

@router.get("/reportes/cumplimiento", status_code=200)
def reporte_cumplimiento_logistico(
    response: Response,
    sucursal_id: Optional[int] = Query(None, description="Filtrar por sucursal origen o destino"),
    clasificar_por: Optional[str] = Query(None, description="Clasificar por: costo, tiempo o prioridad")
):
    resultado, codigo_estado = LogisticaControlador.generar_reporte(sucursal_id=sucursal_id, clasificar_por=clasificar_por)
    response.status_code = codigo_estado
    return resultado