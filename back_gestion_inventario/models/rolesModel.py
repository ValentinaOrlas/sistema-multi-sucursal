from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from conection.conectionDb import Base

if TYPE_CHECKING:
    from models.usuariosModel import UsuarioModel

class RoleModel(Base):
    """
    Entidad roles que se encuentra en la db, donde se especifican los roles existentes.
    """
    __tablename__ = "roles"

    # Identificador único de la tabla 
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Nombre del rol
    nombre: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    
    # Detalle de las responsabilidades del rol (al ser opcional se usa Optional[str])
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relación inversa con usuarios
    usuarios: Mapped[List["UsuarioModel"]] = relationship("UsuarioModel", back_populates="rol")