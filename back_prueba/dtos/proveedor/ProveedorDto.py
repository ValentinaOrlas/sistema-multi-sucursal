from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class ProveedorCreateRequest(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=150)
    contacto: Optional[str] = Field(None, max_length=100)
    condiciones_comerciales: Optional[str] = None
    tiempo_entrega_promedio_dias: int = Field(..., ge=0)

class ProveedorUpdateRequest(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=150)
    contacto: Optional[str] = Field(None, max_length=100)
    condiciones_comerciales: Optional[str] = None
    tiempo_entrega_promedio_dias: Optional[int] = Field(None, ge=0)

class AsociarProductoRequest(BaseModel):
    producto_id: int
    precio_referencia: Optional[float] = Field(None, ge=0)