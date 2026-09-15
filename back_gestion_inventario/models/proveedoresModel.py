from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Integer, Text, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from conection.conectionDb import Base

if TYPE_CHECKING:
    from models.ordenesCompraModel import OrdenCompraModel

class ProveedorModel(Base):
    __tablename__ = "proveedores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    contacto: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    condiciones_comerciales: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tiempo_entrega_promedio_dias: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        CheckConstraint("tiempo_entrega_promedio_dias >= 0", name="check_tiempo_entrega_positivo"),
    )

    # Relaciones
    ordenes_compra: Mapped[List["OrdenCompraModel"]] = relationship("OrdenCompraModel", back_populates="proveedor")