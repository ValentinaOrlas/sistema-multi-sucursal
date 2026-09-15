from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import Integer, Numeric, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from conection.conectionDb import Base

if TYPE_CHECKING:
    from models.ventasModel import VentaModel

class DetalleVentaModel(Base):
    __tablename__ = "detalle_venta"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    venta_id: Mapped[int] = mapped_column(Integer, ForeignKey("ventas.id", ondelete="CASCADE"), nullable=False)
    producto_id: Mapped[int] = mapped_column(Integer, ForeignKey("productos.id"), nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    descuento_aplicado: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0.00)

    __table_args__ = (
        CheckConstraint("cantidad > 0", name="check_cantidad_venta_positiva"),
        CheckConstraint("precio_unitario >= 0", name="check_precio_unitario_venta_positivo"),
    )

    # Relaciones
    venta: Mapped["VentaModel"] = relationship("VentaModel", back_populates="detalles")