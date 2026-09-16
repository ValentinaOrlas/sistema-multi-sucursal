"""Contrato del registro de un producto tecnológico con su ingreso inicial."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

TextoSku = Annotated[str, Field(min_length=1, max_length=100)]
NombreProducto = Annotated[str, Field(min_length=1, max_length=150)]
UnidadMedida = Annotated[str, Field(min_length=1, max_length=50)]
CantidadInicial = Annotated[Decimal, Field(gt=0, max_digits=14, decimal_places=3)]
StockMinimo = Annotated[Decimal, Field(ge=0, max_digits=14, decimal_places=3)]
CostoUnitario = Annotated[Decimal, Field(ge=0, max_digits=18, decimal_places=6)]


class RegistrarProductoDto(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        json_schema_extra={
            "examples": [
                {
                    "sku": "TEC-SSD-001",
                    "nombre": "SSD NVMe 1 TB",
                    "categoria_id": 1,
                    "stock_minimo": 3,
                    "unidad_medida": "unidad",
                    "cantidad_inicial": 10,
                    "costo_unitario": 250000,
                }
            ]
        },
    )
    sku: TextoSku
    nombre: NombreProducto
    descripcion: Annotated[str, Field(max_length=5000)] | None = None
    categoria_id: Annotated[int, Field(gt=0)]
    stock_minimo: StockMinimo
    unidad_medida: UnidadMedida
    cantidad_inicial: CantidadInicial
    costo_unitario: CostoUnitario


class RespuestaBase(BaseModel):
    pass


class ProductoCreadoDto(RespuestaBase):
    id: int
    sku: str
    nombre: str
    descripcion: str | None = None
    categoria_id: int
    unidad_medida: str


class InventarioInicialDto(RespuestaBase):
    id: int
    producto_id: int
    sucursal_id: int
    stock_actual: Decimal
    stock_minimo_local: Decimal
    costo_promedio_ponderado: Decimal


class MovimientoInicialDto(RespuestaBase):
    id: int
    producto_id: int
    sucursal_id: int
    usuario_id: int
    tipo_movimiento: Literal["INGRESO"]
    motivo: str
    cantidad: Decimal
    stock_resultante: Decimal
    costo_unitario: Decimal
    fecha_movimiento: datetime

    @field_validator("fecha_movimiento")
    @classmethod
    def fecha_utc(cls, value: datetime):
        # La conexión existente almacena fechas sin zona en UTC.
        return (
            value.replace(tzinfo=timezone.utc)
            if value.tzinfo is None
            else value.astimezone(timezone.utc)
        )


class RegistroProductoRespuestaDto(BaseModel):
    producto: ProductoCreadoDto
    inventario: InventarioInicialDto
    movimiento: MovimientoInicialDto
