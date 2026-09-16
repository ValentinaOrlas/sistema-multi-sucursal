"""Historia: registrar un producto tecnológico y sus existencias iniciales."""

from dataclasses import dataclass
from datetime import datetime, timezone

from dtos.producto_dto import RegistrarProductoDto
from exceptions.producto_exceptions import (
    CategoriaNoEncontrada,
    OperadorRequerido,
    SkuDuplicado,
    SucursalNoDisponible,
    UsuarioNoAutenticado,
)
from repositories.producto_repository import (
    ProductoRepository,
)

MOTIVO_REGISTRO = "Registro inicial de producto tecnológico"


@dataclass(frozen=True)
class ResultadoRegistroProducto:
    producto: dict
    inventario: dict
    movimiento: dict


class ProductoService:
    def __init__(self, repository: ProductoRepository):
        self.repository = repository

    def registrar(
        self, datos: RegistrarProductoDto, usuario_id: int
    ) -> ResultadoRegistroProducto:
        operador = self.repository.buscar_usuario(usuario_id)
        if operador is None or not operador["activo"]:
            raise UsuarioNoAutenticado()
        if operador["rol_nombre"] != "OPERADOR_INVENTARIO":
            raise OperadorRequerido()
        if operador["sucursal_id"] is None:
            raise SucursalNoDisponible()
        sucursal = self.repository.bloquear_sucursal(operador["sucursal_id"])
        if sucursal is None or not sucursal["activa"]:
            raise SucursalNoDisponible()
        if self.repository.buscar_categoria(datos.categoria_id) is None:
            raise CategoriaNoEncontrada()
        if self.repository.buscar_por_sku(datos.sku) is not None:
            raise SkuDuplicado()

        producto = self.repository.insertar_producto(
            dict(
                sku=datos.sku,
                nombre=datos.nombre,
                descripcion=datos.descripcion,
                categoria_id=datos.categoria_id,
                unidad_medida=datos.unidad_medida,
            )
        )
        # El mínimo capturado es local. No se copia a stock_minimo_global.
        inventario = self.repository.insertar_inventario(
            dict(
                producto_id=producto["id"],
                sucursal_id=sucursal["id"],
                stock_actual=datos.cantidad_inicial,
                stock_minimo_local=datos.stock_minimo,
                costo_promedio_ponderado=datos.costo_unitario,
            )
        )
        movimiento = self.repository.insertar_movimiento(
            dict(
                producto_id=producto["id"],
                sucursal_id=sucursal["id"],
                usuario_id=operador["id"],
                tipo_movimiento="INGRESO",
                motivo=MOTIVO_REGISTRO,
                cantidad=datos.cantidad_inicial,
                stock_resultante=datos.cantidad_inicial,
                costo_unitario=datos.costo_unitario,
                fecha_movimiento=datetime.now(timezone.utc).replace(tzinfo=None),
            )
        )
        # Los tres inserts comparten sesión. La conexión confirma al terminar la
        # petición; cualquier fallo revierte todo el registro.
        return ResultadoRegistroProducto(producto, inventario, movimiento)
