from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from conection.conectionDb import Base

if TYPE_CHECKING:
    from models.detalleTransferenciaModel import DetalleTransferenciaModel

class TransferenciaModel(Base):
    __tablename__ = "transferencias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sucursal_origen_id: Mapped[int] = mapped_column(Integer, ForeignKey("sucursales.id"), nullable=False)
    sucursal_destino_id: Mapped[int] = mapped_column(Integer, ForeignKey("sucursales.id"), nullable=False)
    usuario_solicitante_id: Mapped[int] = mapped_column(Integer, ForeignKey("usuarios.id"), nullable=False)
    estado: Mapped[str] = mapped_column(String(50), nullable=False, default="SOLICITADA")
    prioridad: Mapped[str] = mapped_column(String(20), nullable=False, default="MEDIA")
    transportista: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    fecha_estimada_llegada: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    fecha_real_llegada: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    # Relaciones
    detalles: Mapped[List["DetalleTransferenciaModel"]] = relationship("DetalleTransferenciaModel", back_populates="transferencia", cascade="all, delete-orphan")