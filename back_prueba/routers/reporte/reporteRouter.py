from fastapi import APIRouter, Response, Query
from fastapi.responses import StreamingResponse
from typing import Optional
from controllers.reporte.reporteControlador import ReportesControlador
from dtos.reportes.ReporteDto import TipoReporte, FormatoReporte

router = APIRouter(
    prefix="/api/reportes",
    tags=["Módulo de Reportes"]
)

@router.get("/descargar")
def descargar_reporte(
    response: Response,
    tipo: TipoReporte = Query(..., description="Tipo de reporte (ventas, movimientos, transferencias)"),
    formato: FormatoReporte = Query(..., description="Formato del archivo (pdf, excel)"),
    fecha_inicio: str = Query(..., description="Fecha inicio (YYYY-MM-DD)"),
    fecha_fin: str = Query(..., description="Fecha fin (YYYY-MM-DD)"),
    sucursal_id: Optional[int] = Query(None, description="Opcional: Filtrar por ID de sucursal")
):
    resultado, codigo_estado = ReportesControlador.generar_reporte(
        tipo=tipo.value,
        formato=formato.value,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        sucursal_id=sucursal_id
    )

    # Si hay un error (ej. 404 No hay datos, 400 Bad Request) devolvemos el JSON normal
    if codigo_estado != 200:
        response.status_code = codigo_estado
        return resultado

    # Si todo sale bien, extraemos el stream y lo enviamos como archivo descargable
    return StreamingResponse(
        resultado["stream"], 
        media_type=resultado["media_type"],
        headers={"Content-Disposition": f"attachment; filename={resultado['filename']}"}
    )