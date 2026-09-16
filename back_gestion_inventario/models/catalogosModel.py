from decimal import Decimal
from sqlalchemy import ForeignKey, String, Numeric, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from conection.conectionDb import Base


class UnidadProductoModel(Base):
    __tablename__ = "unidades_producto"
    id: Mapped[int] = mapped_column(primary_key=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"), index=True)
    nombre: Mapped[str] = mapped_column(String(50))
    factor: Mapped[Decimal] = mapped_column(Numeric(14, 6))
    __table_args__ = (
        UniqueConstraint("producto_id", "nombre", name="uq_unidad_producto"),
        CheckConstraint("factor > 0", name="ck_factor_unidad"),
    )


class ListaPrecioModel(Base):
    __tablename__ = "listas_precios"
    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True)


class PrecioProductoModel(Base):
    __tablename__ = "precios_producto"
    id: Mapped[int] = mapped_column(primary_key=True)
    lista_id: Mapped[int] = mapped_column(ForeignKey("listas_precios.id"), index=True)
    producto_id: Mapped[int] = mapped_column(ForeignKey("productos.id"), index=True)
    precio: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    __table_args__ = (
        UniqueConstraint("lista_id", "producto_id", name="uq_precio_producto"),
        CheckConstraint("precio >= 0", name="ck_precio_lista"),
    )
