from typing import Literal

from controllers import reportes_controller as controller
from core.dependencies import Db, User
from fastapi import APIRouter, Query

router = APIRouter(tags=["Análisis"])


@router.get("/dashboard")
def dashboard(db: Db, user: User, sucursal_id: int | None = None):
    return controller.dashboard(db, user, sucursal_id)


@router.get("/analisis/demanda")
def demanda(
    db: Db,
    user: User,
    sucursal_id: int | None = None,
    dias: int = Query(30, ge=7, le=365),
):
    return controller.demanda(db, user, sucursal_id, dias)


@router.get("/reportes/logistica")
def logistica(
    db: Db,
    user: User,
    sucursal_id: int | None = None,
    dias: int = Query(90, ge=1, le=365),
    ordenar_por: Literal["prioridad", "costo", "tiempo"] = "prioridad",
):
    return controller.logistica(db, user, sucursal_id, dias, ordenar_por)
