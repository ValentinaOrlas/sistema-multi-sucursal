from decimal import Decimal
from sqlalchemy import Integer, Numeric, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from conection.conectionDb import Base

class InventarioSucursalModel(Base):
    __tablename__ = "inventario_sucursal"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sucursal_id: Mapped[int] = mapped_column(Integer, ForeignKey("sucursales.id"), nullable=False)
    producto_id: Mapped[int] = mapped_column(Integer, ForeignKey("productos.id"), nullable=False)
    stock_actual: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stock_minimo_local: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    costo_promedio_ponderado: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0.00)

    __table_args__ = (
        UniqueConstraint("sucursal_id", "producto_id", name="uq_sucursal_producto"),
        CheckConstraint("stock_actual >= 0", name="check_stock_actual_positivo"),
        CheckConstraint("stock_minimo_local >= 0", name="check_stock_minimo_local_positivo"),
        CheckConstraint("costo_promedio_ponderado >= 0", name="check_costo_promedio_positivo"),
    )