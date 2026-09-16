"""Errores del caso de uso, independientes de FastAPI y SQLAlchemy."""


class ErrorRegistroProducto(Exception):
    codigo = "REGISTRO_PRODUCTO_ERROR"


class SkuDuplicado(ErrorRegistroProducto):
    codigo = "SKU_DUPLICADO"

    def __init__(self):
        super().__init__("Ya existe un producto con ese SKU en el sistema.")


class CategoriaNoEncontrada(ErrorRegistroProducto):
    codigo = "CATEGORIA_NO_ENCONTRADA"

    def __init__(self):
        super().__init__("La categoría seleccionada no existe.")


class UsuarioNoAutenticado(ErrorRegistroProducto):
    codigo = "USUARIO_NO_AUTENTICADO"

    def __init__(self):
        super().__init__("La sesión no corresponde a un usuario activo.")


class OperadorRequerido(ErrorRegistroProducto):
    codigo = "OPERADOR_REQUERIDO"

    def __init__(self):
        super().__init__("Solo OPERADOR_INVENTARIO puede registrar un producto.")


class SucursalNoDisponible(ErrorRegistroProducto):
    codigo = "SUCURSAL_NO_DISPONIBLE"

    def __init__(self):
        super().__init__("El operador debe tener una sucursal existente y activa.")
