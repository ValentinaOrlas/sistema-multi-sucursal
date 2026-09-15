from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from dto.categoriasDto import CategoriaResponse

class ProductoBase(BaseModel):
    sku: str
    nombre: str
    descripcion: Optional[str] = None
    unidad_medida: str
    stock_minimo_global: int = Field(ge=0, default=0)

class ProductoCreate(ProductoBase):
    categoria_id: int

class ProductoUpdate(BaseModel):
    sku: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    categoria_id: Optional[int] = None
    unidad_medida: Optional[str] = None
    stock_minimo_global: Optional[int] = Field(default=None, ge=0)

class ProductoResponse(ProductoBase):
    id: int
    categoria_id: int
    categoria: Optional[CategoriaResponse] = None

    model_config = ConfigDict(from_attributes=True)