from service.gestion_inventario.InventarioService import InventarioService

class InventarioControlador:
    productos = staticmethod(InventarioService.productos)
    producto = staticmethod(InventarioService.producto)
    crear = staticmethod(InventarioService.crear)
    actualizar = staticmethod(InventarioService.actualizar)
    eliminar = staticmethod(InventarioService.eliminar)
    categorias = staticmethod(InventarioService.categorias)
    crear_categoria = staticmethod(InventarioService.crear_categoria)
    sucursales = staticmethod(InventarioService.sucursales)
    inventario = staticmethod(InventarioService.inventario)
    minimo = staticmethod(InventarioService.minimo)
    registrar = staticmethod(InventarioService.registrar)
    movimientos = staticmethod(InventarioService.movimientos)
    alertas = staticmethod(InventarioService.alertas)
