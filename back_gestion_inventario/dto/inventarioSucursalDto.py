from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from dto.productosDto import ProductoResponse

class InventarioSucursalBase(BaseModel):
    sucursal_id: int
    producto_id: int
    stock_actual: int = Field(ge=0, default=0)
    stock_minimo_local: int = Field(ge=0, default=0)
    costo_promedio_ponderado: Decimal = Field(ge=0, default=Decimal("0.00"))

class InventarioSucursalCreate(InventarioSucursalBase):
    pass

class InventarioSucursalUpdate(BaseModel):
    stock_actual: Optional[int] = Field(default=None, ge=0)
    stock_minimo_local: Optional[int] = Field(default=None, ge=0)
    costo_promedio_ponderado: Optional[Decimal] = Field(default=None, ge=0)

class InventarioSucursalResponse(InventarioSucursalBase):
    id: int
    producto: Optional[ProductoResponse] = None

    model_config = ConfigDict(from_attributes=True)