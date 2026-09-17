from decimal import Decimal
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field

Cantidad = Annotated[Decimal, Field(gt=0, max_digits=14, decimal_places=3)]
Minimo = Annotated[Decimal, Field(ge=0, max_digits=14, decimal_places=3)]
Costo = Annotated[Decimal, Field(ge=0, max_digits=18, decimal_places=6)]

class ProductoUpdateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    sku: str = Field(min_length=1, max_length=100)
    nombre: str = Field(min_length=1, max_length=150)
    descripcion: str = Field(default='', max_length=5000)
    categoria_id: int = Field(gt=0)

class ProductoCreateRequest(ProductoUpdateRequest):
    unidad_medida: str = Field(min_length=1, max_length=50)
    cantidad_inicial: Cantidad
    stock_minimo: Minimo
    costo_unitario: Costo

class MovimientoRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    sucursal_id: int = Field(gt=0)
    producto_id: int = Field(gt=0)
    cantidad: Cantidad
    motivo: str = Field(min_length=1, max_length=100)
    tipo_movimiento: Literal['INGRESO', 'RETIRO'] | None = None
    costo_unitario: Costo | None = None
    usuario_id: int | None = None

class MinimoRequest(BaseModel):
    sucursal_id: int = Field(gt=0)
    producto_id: int = Field(gt=0)
    stock_minimo_local: Minimo

class CategoriaRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    nombre: str = Field(min_length=1, max_length=100)
    descripcion: str = ''
