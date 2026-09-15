from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

# Detalle de la venta
class DetalleVentaCreate(BaseModel):
    producto_id: int
    cantidad: int = Field(gt=0)
    precio_unitario: Decimal = Field(ge=0)
    descuento_aplicado: Decimal = Field(ge=0, default=Decimal("0.00"))

class DetalleVentaResponse(DetalleVentaCreate):
    id: int
    venta_id: int

    model_config = ConfigDict(from_attributes=True)

# Cabecera de la venta
class VentaCreate(BaseModel):
    sucursal_id: int
    usuario_id: int
    detalles: List[DetalleVentaCreate]

class VentaResponse(BaseModel):
    id: int
    sucursal_id: int
    usuario_id: int
    fecha_venta: datetime
    total_venta: Decimal
    detalles: List[DetalleVentaResponse] = []

    model_config = ConfigDict(from_attributes=True)