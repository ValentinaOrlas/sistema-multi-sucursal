from datetime import datetime
from decimal import Decimal
from typing import List, TYPE_CHECKING
from sqlalchemy import Integer, Numeric, DateTime, ForeignKey, func, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from conection.conectionDb import Base

if TYPE_CHECKING:
    from models.detalleVentaModel import DetalleVentaModel

class VentaModel(Base):
    __tablename__ = "ventas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sucursal_id: Mapped[int] = mapped_column(Integer, ForeignKey("sucursales.id"), nullable=False)
    usuario_id: Mapped[int] = mapped_column(Integer, ForeignKey("usuarios.id"), nullable=False)
    fecha_venta: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    total_venta: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0.00)

    __table_args__ = (
        CheckConstraint("total_venta >= 0", name="check_total_venta_positivo"),
    )

    # Relaciones
    detalles: Mapped[List["DetalleVentaModel"]] = relationship("DetalleVentaModel", back_populates="venta", cascade="all, delete-orphan")