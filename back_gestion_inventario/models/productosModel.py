from sqlalchemy import Numeric
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Integer, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from conection.conectionDb import Base

if TYPE_CHECKING:
    from models.categoriasModel import CategoriaModel


class ProductoModel(Base):
    __tablename__ = "productos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sku: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    categoria_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("categorias.id"), nullable=False
    )
    unidad_medida: Mapped[str] = mapped_column(String(50), nullable=False)
    stock_minimo_global: Mapped[Decimal] = mapped_column(
        Numeric(14, 3), nullable=False, default=0
    )

    __table_args__ = (
        CheckConstraint(
            "stock_minimo_global >= 0", name="check_stock_minimo_global_positivo"
        ),
    )

    # Relaciones
    categoria: Mapped["CategoriaModel"] = relationship(
        "CategoriaModel", back_populates="productos"
    )
