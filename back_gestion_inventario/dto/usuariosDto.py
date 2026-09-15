from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict
from dto.rolesDto import RoleResponse
from dto.sucursalesDto import SucursalResponse

class UsuarioBase(BaseModel):
    nombre: str
    email: EmailStr

class UsuarioCreate(UsuarioBase):
    password: str
    rol_id: int
    sucursal_id: Optional[int] = None

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    rol_id: Optional[int] = None
    sucursal_id: Optional[int] = None
    activo: Optional[bool] = None

class UsuarioResponse(UsuarioBase):
    id: int
    rol_id: int
    sucursal_id: Optional[int] = None
    activo: bool
    rol: Optional[RoleResponse] = None
    sucursal: Optional[SucursalResponse] = None

    model_config = ConfigDict(from_attributes=True)