from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import Integer, Numeric, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from conection.conectionDb import Base

if TYPE_CHECKING:
    from models.ordenesCompraModel import OrdenCompraModel


class DetalleOrdenCompraModel(Base):
    __tablename__ = "detalle_orden_compra"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    orden_compra_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ordenes_compra.id", ondelete="CASCADE"), nullable=False
    )
    producto_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("productos.id"), nullable=False
    )
    cantidad: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    descuento: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=0.00
    )

    __table_args__ = (
        CheckConstraint("descuento BETWEEN 0 AND 100", name="ck_descuento_rango"),
        CheckConstraint("cantidad > 0", name="check_cantidad_orden_positiva"),
        CheckConstraint(
            "precio_unitario >= 0", name="check_precio_unitario_orden_positivo"
        ),
    )

    # Relaciones
    orden_compra: Mapped["OrdenCompraModel"] = relationship(
        "OrdenCompraModel", back_populates="detalles"
    )
