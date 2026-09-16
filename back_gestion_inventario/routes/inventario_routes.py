from controllers import inventario_controller as controller
from core.dependencies import Db, User
from dtos import schemas as s
from fastapi import APIRouter, Query

router = APIRouter(tags=["Inventario"])


@router.get("/inventario", response_model=list[s.InventarioSucursalResponse])
def listado(
    db: Db,
    user: User,
    sucursal_id: int | None = None,
    producto_id: int | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
):
    return controller.listado(db, user, sucursal_id, producto_id, offset, limit)


@router.post(
    "/inventario", response_model=s.InventarioSucursalResponse, status_code=201
)
def configurar(payload: s.InventarioSucursalCreate, db: Db, user: User):
    return controller.configurar(payload, db, user)


@router.post(
    "/inventario/movimientos", response_model=s.MovimientoResponse, status_code=201
)
def registrar(payload: s.MovimientoCreate, db: Db, user: User):
    return controller.registrar(payload, db, user)


@router.get("/inventario/movimientos", response_model=list[s.MovimientoResponse])
def movimientos(
    db: Db,
    user: User,
    sucursal_id: int | None = None,
    producto_id: int | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
):
    return controller.movimientos(db, user, sucursal_id, producto_id, offset, limit)


@router.get("/inventario/alertas", response_model=list[s.InventarioSucursalResponse])
def alertas(db: Db, user: User, sucursal_id: int | None = None):
    return controller.alertas(db, user, sucursal_id)
