from fastapi import APIRouter, Response
from controllers.dashboard.dashboardControlador import DashboardControlador

router = APIRouter(
    prefix="/api/dashboard",
    tags=["Módulo de Análisis y Visualización (Dashboard)"]
)

@router.get("/sucursales/{sucursal_id}", status_code=200)
def dashboard_por_sucursal(sucursal_id: int, response: Response):
    resultado, codigo_estado = DashboardControlador.obtener_dashboard_sucursal(sucursal_id)
    response.status_code = codigo_estado
    return resultado

@router.get("/admin/comparativa", status_code=200)
def dashboard_comparativo_administrativo(response: Response):
    resultado, codigo_estado = DashboardControlador.obtener_dashboard_administrativo()
    response.status_code = codigo_estado
    return resultado