from decimal import Decimal
from pydantic import BaseModel, Field
from dtos.gestion_inventario.inventarioDto import Cantidad, Costo

class DetalleOrdenCompraRequest(BaseModel):
    producto_id: int = Field(gt=0)
    cantidad: Cantidad
    precio_unitario: Costo
    descuento: Decimal = Field(default=Decimal(0), ge=0, le=100, decimal_places=2)

class OrdenCompraCreateRequest(BaseModel):
    proveedor_id: int = Field(gt=0)
    sucursal_destino_id: int = Field(gt=0)
    usuario_id: int | None = None
    plazo_pago_dias: int = Field(default=0, ge=0)
    detalles: list[DetalleOrdenCompraRequest] = Field(min_length=1)

class RecibirOrdenRequest(BaseModel):
    usuario_id: int | None = None
