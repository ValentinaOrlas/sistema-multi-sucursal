from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from conection.conectionDb import Base

if TYPE_CHECKING:
    from models.proveedoresModel import ProveedorModel
    from models.detalleOrdenCompraModel import DetalleOrdenCompraModel

class OrdenCompraModel(Base):
    __tablename__ = "ordenes_compra"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    proveedor_id: Mapped[int] = mapped_column(Integer, ForeignKey("proveedores.id"), nullable=False)
    sucursal_destino_id: Mapped[int] = mapped_column(Integer, ForeignKey("sucursales.id"), nullable=False)
    usuario_id: Mapped[int] = mapped_column(Integer, ForeignKey("usuarios.id"), nullable=False)
    estado: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDIENTE")
    fecha_creacion: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    fecha_recepcion: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relaciones
    proveedor: Mapped["ProveedorModel"] = relationship("ProveedorModel", back_populates="ordenes_compra")
    detalles: Mapped[List["DetalleOrdenCompraModel"]] = relationship("DetalleOrdenCompraModel", back_populates="orden_compra", cascade="all, delete-orphan")