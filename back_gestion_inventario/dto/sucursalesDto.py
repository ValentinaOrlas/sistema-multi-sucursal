from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class SucursalBase(BaseModel):
    nombre: str
    ubicacion: str

class SucursalCreate(SucursalBase):
    activa: Optional[bool] = True

class SucursalUpdate(BaseModel):
    nombre: Optional[str] = None
    ubicacion: Optional[str] = None
    activa: Optional[bool] = None

class SucursalResponse(SucursalBase):
    id: int
    activa: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)