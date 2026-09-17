from service.proveedor.ProveedorService import ProveedoresService

class ProveedoresControlador:

    @staticmethod
    def crear_proveedor(datos: dict) -> tuple:
        return ProveedoresService.crear_proveedor(datos)

    @staticmethod
    def listar_proveedores() -> tuple:
        return ProveedoresService.listar_proveedores()

    @staticmethod
    def obtener_proveedor(proveedor_id: int) -> tuple:
        return ProveedoresService.obtener_proveedor_detalle(proveedor_id)

    @staticmethod
    def actualizar_proveedor(proveedor_id: int, datos: dict) -> tuple:
        return ProveedoresService.actualizar_proveedor(proveedor_id, datos)

    @staticmethod
    def asociar_producto(proveedor_id: int, datos: dict) -> tuple:
        return ProveedoresService.asociar_producto_proveedor(proveedor_id, datos)

    @staticmethod
    def evaluar_tiempos(proveedor_id: int) -> tuple:
        return ProveedoresService.evaluar_tiempos_entrega(proveedor_id)