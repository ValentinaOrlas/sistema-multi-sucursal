from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Integer, Boolean, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from conection.conectionDb import Base

if TYPE_CHECKING:
    from models.usuariosModel import UsuarioModel

class SucursalesModel(Base):
    """
    Entidad sucursales dentro de la DB la cual almacena la información de las sucursales existentes.
    """
    __tablename__ = "sucursales"

    # Identificador único de la tabla 
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Nombre de la sucursal
    nombre: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)

    # Dónde se encuentra ubicada
    ubicacion: Mapped[str] = mapped_column(String(255), nullable=False)

    # Si se encuentra o no activa
    activa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # La fecha en que fue registrada
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, server_default=func.now())

    # Relación inversa con usuarios
    usuarios: Mapped[List["UsuarioModel"]] = relationship("UsuarioModel", back_populates="sucursal")