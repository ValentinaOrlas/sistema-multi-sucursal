"""Coordina el servicio y construye la respuesta del caso de uso."""

from dtos.producto_dto import (
    RegistrarProductoDto,
    RegistroProductoRespuestaDto,
)
from service.producto_service import ProductoService


class ProductoController:
    def __init__(self, service: ProductoService):
        self.service = service

    def registrar(
        self, datos: RegistrarProductoDto, usuario_id: int
    ) -> RegistroProductoRespuestaDto:
        resultado = self.service.registrar(datos, usuario_id)
        return RegistroProductoRespuestaDto(
            producto=resultado.producto,
            inventario=resultado.inventario,
            movimiento=resultado.movimiento,
        )
