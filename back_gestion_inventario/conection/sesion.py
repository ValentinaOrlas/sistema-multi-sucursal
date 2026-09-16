"""Reutiliza la conexión existente; una sesión y una transacción por petición."""

from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session
from conection.conectionDb import getDb

# Confirmar el commit antes de enviar una respuesta exitosa.
SesionInventario = Annotated[Session, Depends(getDb, scope="function")]
