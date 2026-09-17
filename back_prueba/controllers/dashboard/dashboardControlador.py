from service.dashboard.DashboardService import DashboardService

class DashboardControlador:

    @staticmethod
    def obtener_dashboard_sucursal(sucursal_id: int) -> tuple:
        return DashboardService.obtener_dashboard_sucursal(sucursal_id)

    @staticmethod
    def obtener_dashboard_administrativo() -> tuple:
        return DashboardService.obtener_dashboard_administrativo()