from typing import Optional
from pydantic import BaseModel, ConfigDict

# Base con atributos compartidos
class RoleBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

