"""Ruta y composición de dependencias para registrar productos."""

from conection.sesion import SesionInventario
from controllers.producto_controller import ProductoController
from dtos.producto_dto import (
    RegistrarProductoDto,
    RegistroProductoRespuestaDto,
)
from exceptions.producto_exceptions import (
    UsuarioNoAutenticado,
)
from fastapi import APIRouter, Request
from repositories.producto_repository import (
    ProductoRepository,
)
from service.producto_service import ProductoService

router = APIRouter(tags=["Gestión de inventario - Registro de producto"])


@router.post(
    "/productos",
    status_code=201,
    response_model=RegistroProductoRespuestaDto,
    summary="Registrar producto tecnológico con existencias iniciales",
    description="Exclusivo de OPERADOR_INVENTARIO. Crea producto, inventario local e ingreso auditable en una transacción.",
    openapi_extra={"security": [{"HTTPBearer": []}]},
    responses={
        401: {"description": "Sesión ausente, inválida o usuario inactivo"},
        403: {"description": "Rol distinto de operador o sucursal no disponible"},
        404: {"description": "Categoría inexistente"},
        409: {"description": "SKU duplicado"},
    },
)
def registrar_producto(
    datos: RegistrarProductoDto, request: Request, db: SesionInventario
):
    usuario_id = getattr(request.state, "registro_producto_usuario_id", None)
    if usuario_id is None:
        raise UsuarioNoAutenticado()
    controller = ProductoController(ProductoService(ProductoRepository(db)))
    return controller.registrar(datos, usuario_id)
