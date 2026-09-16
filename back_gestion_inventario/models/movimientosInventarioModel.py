from sqlalchemy import Numeric
from decimal import Decimal
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, func, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from conection.conectionDb import Base


class MovimientosInventarioModel(Base):
    __tablename__ = "movimientos_inventario"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sucursal_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sucursales.id"), nullable=False
    )
    producto_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("productos.id"), nullable=False
    )
    cantidad: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    tipo_movimiento: Mapped[str] = mapped_column(String(20), nullable=False)
    motivo: Mapped[str] = mapped_column(String(100), nullable=False)
    stock_resultante: Mapped[Decimal] = mapped_column(Numeric(14, 3), nullable=False)
    fecha_movimiento: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    # Legacy rows retain NULL instead of inventing a responsible user.
    usuario_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("usuarios.id"), nullable=True
    )
    venta_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("ventas.id"), nullable=True
    )
    orden_compra_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("ordenes_compra.id"), nullable=True
    )
    transferencia_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("transferencias.id"), nullable=True
    )
    costo_unitario: Mapped[Decimal] = mapped_column(
        Numeric(18, 6), nullable=False, default=0
    )

    __table_args__ = (
        CheckConstraint("cantidad > 0", name="check_cantidad_movimiento_positiva"),
        CheckConstraint(
            "stock_resultante >= 0", name="check_stock_resultante_positivo"
        ),
        CheckConstraint(
            "tipo_movimiento IN ('INGRESO', 'RETIRO')",
            name="check_tipo_movimiento_valido",
        ),
    )
