from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, func, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from conection.conectionDb import Base

class MovimientosInventarioModel(Base):
    __tablename__ = "movimientos_inventario"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sucursal_id: Mapped[int] = mapped_column(Integer, ForeignKey("sucursales.id"), nullable=False)
    producto_id: Mapped[int] = mapped_column(Integer, ForeignKey("productos.id"), nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    tipo_movimiento: Mapped[str] = mapped_column(String(20), nullable=False)
    motivo: Mapped[str] = mapped_column(String(100), nullable=False)
    stock_resultante: Mapped[int] = mapped_column(Integer, nullable=False)
    fecha_movimiento: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        CheckConstraint("cantidad > 0", name="check_cantidad_movimiento_positiva"),
        CheckConstraint("stock_resultante >= 0", name="check_stock_resultante_positivo"),
        CheckConstraint("tipo_movimiento IN ('INGRESO', 'RETIRO')", name="check_tipo_movimiento_valido"),
    )