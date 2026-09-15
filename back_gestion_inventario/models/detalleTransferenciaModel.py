from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from conection.conectionDb import Base

if TYPE_CHECKING:
    from models.transferenciasModel import TransferenciaModel

class DetalleTransferenciaModel(Base):
    __tablename__ = "detalle_transferencia"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    transferencia_id: Mapped[int] = mapped_column(Integer, ForeignKey("transferencias.id", ondelete="CASCADE"), nullable=False)
    producto_id: Mapped[int] = mapped_column(Integer, ForeignKey("productos.id"), nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    cantidad_solicitada: Mapped[int] = mapped_column(Integer, nullable=False)
    cantidad_enviada: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cantidad_recibida: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    faltantes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tratamiento_faltante: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    __table_args__ = (
        CheckConstraint("cantidad > 0", name="check_cantidad_transf_positiva"),
        CheckConstraint("cantidad_solicitada > 0", name="check_cantidad_solic_positiva"),
        CheckConstraint("cantidad_enviada >= 0", name="check_cantidad_env_positiva"),
        CheckConstraint("cantidad_recibida >= 0", name="check_cantidad_rec_positiva"),
        CheckConstraint("faltantes >= 0", name="check_faltantes_positivo"),
    )

    # Relaciones
    transferencia: Mapped["TransferenciaModel"] = relationship("TransferenciaModel", back_populates="detalles")