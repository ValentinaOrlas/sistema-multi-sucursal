from decimal import Decimal
from pydantic import BaseModel, Field
from dtos.gestion_inventario.inventarioDto import Cantidad, Costo

class DetalleVentaRequest(BaseModel):
    producto_id: int = Field(gt=0)
    cantidad: Cantidad
    precio_unitario: Costo | None = None
    descuento_aplicado: Decimal = Field(default=Decimal(0), ge=0, le=100, decimal_places=2)

class VentaCreateRequest(BaseModel):
    sucursal_id: int = Field(gt=0)
    usuario_id: int | None = None
    lista_precio_id: int | None = Field(default=None, gt=0)
    detalles: list[DetalleVentaRequest] = Field(min_length=1)
