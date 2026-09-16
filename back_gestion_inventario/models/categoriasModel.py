from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from conection.conectionDb import Base

if TYPE_CHECKING:
    from models.productosModel import ProductoModel


class CategoriaModel(Base):
    __tablename__ = "categorias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relaciones
    productos: Mapped[List["ProductoModel"]] = relationship(
        "ProductoModel", back_populates="categoria"
    )
