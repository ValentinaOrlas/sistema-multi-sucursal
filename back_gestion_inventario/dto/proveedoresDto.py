from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class ProveedorBase(BaseModel):
    nombre: str
    contacto: Optional[str] = None
    condiciones_comerciales: Optional[str] = None
    tiempo_entrega_promedio_dias: int = Field(ge=0, default=0)

class ProveedorCreate(ProveedorBase):
    pass

class ProveedorUpdate(BaseModel):
    nombre: Optional[str] = None
    contacto: Optional[str] = None
    condiciones_comerciales: Optional[str] = None
    tiempo_entrega_promedio_dias: Optional[int] = Field(default=None, ge=0)

class ProveedorResponse(ProveedorBase):
    id: int

    model_config = ConfigDict(from_attributes=True)