from pydantic import BaseModel, Field
from typing import List, Optional

class DetalleTransferenciaRequest(BaseModel):
    producto_id: int
    cantidad_solicitada: int = Field(..., gt=0)

class TransferenciaCreateRequest(BaseModel):
    sucursal_origen_id: int
    sucursal_destino_id: int
    usuario_solicitante_id: int
    prioridad: str = Field(default="MEDIA", pattern="^(ALTA|MEDIA|BAJA)$")
    detalles: List[DetalleTransferenciaRequest]

class PrepararEnvioDetalleRequest(BaseModel):
    producto_id: int
    cantidad_enviada: int = Field(..., ge=0)

class PrepararEnvioRequest(BaseModel):
    detalles: List[PrepararEnvioDetalleRequest]
    transportista: Optional[str] = None
    fecha_estimada_llegada: Optional[str] = None  # Formato string ISO o timestamp

class DetalleRecepcionItem(BaseModel):
    producto_id: int
    cantidad_recibida: int = Field(..., ge=0)
    tratamiento_faltante: Optional[str] = Field(None, pattern="^(REENVIO|AJUSTE|RECLAMACION|None)$")

class RecibirTransferenciaRequest(BaseModel):
    detalles: List[DetalleRecepcionItem]