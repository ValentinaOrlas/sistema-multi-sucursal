from controllers import operaciones_controller as controller
from core.dependencies import Db, User
from dtos import schemas as s
from fastapi import APIRouter, Query

router = APIRouter(tags=["Operaciones"])


@router.post("/ventas", response_model=s.VentaResponse, status_code=201)
def crear_venta(payload: s.VentaCreate, db: Db, user: User):
    return controller.crear_venta(payload, db, user)


@router.get("/ventas", response_model=list[s.VentaResponse])
def ventas(
    db: Db,
    user: User,
    sucursal_id: int | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
):
    return controller.ventas(db, user, sucursal_id, offset, limit)


@router.get("/ventas/{identity}", response_model=s.VentaResponse)
def venta(identity: int, db: Db, user: User):
    return controller.venta(identity, db, user)


@router.post("/compras", response_model=s.OrdenCompraResponse, status_code=201)
def crear_compra(payload: s.OrdenCompraCreate, db: Db, user: User):
    return controller.crear_compra(payload, db, user)


@router.get("/compras", response_model=list[s.OrdenCompraResponse])
def compras(
    db: Db,
    user: User,
    sucursal_id: int | None = None,
    proveedor_id: int | None = None,
    producto_id: int | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
):
    return controller.compras(
        db, user, sucursal_id, proveedor_id, producto_id, offset, limit
    )


@router.get("/compras/{identity}", response_model=s.OrdenCompraResponse)
def compra(identity: int, db: Db, user: User):
    return controller.compra(identity, db, user)


@router.post("/compras/{identity}/recibir", response_model=s.OrdenCompraResponse)
def recibir_compra(identity: int, db: Db, user: User):
    return controller.recibir_compra(identity, db, user)


@router.post("/compras/{identity}/cancelar", response_model=s.OrdenCompraResponse)
def cancelar_compra(identity: int, db: Db, user: User):
    return controller.cancelar_compra(identity, db, user)


@router.post("/transferencias", response_model=s.TransferenciaResponse, status_code=201)
def crear_transferencia(payload: s.TransferenciaCreate, db: Db, user: User):
    return controller.crear_transferencia(payload, db, user)


@router.get("/transferencias", response_model=list[s.TransferenciaResponse])
def transferencias(
    db: Db,
    user: User,
    estado: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
):
    return controller.transferencias(db, user, estado, offset, limit)


@router.get("/transferencias/{identity}", response_model=s.TransferenciaResponse)
def transferencia(identity: int, db: Db, user: User):
    return controller.transferencia(identity, db, user)


@router.post(
    "/transferencias/{identity}/preparar", response_model=s.TransferenciaResponse
)
def preparar(identity: int, payload: s.PrepararTransferencia, db: Db, user: User):
    return controller.preparar(identity, payload, db, user)


@router.post(
    "/transferencias/{identity}/despachar", response_model=s.TransferenciaResponse
)
def despachar(identity: int, payload: s.DespacharTransferencia, db: Db, user: User):
    return controller.despachar(identity, payload, db, user)


@router.post(
    "/transferencias/{identity}/recibir", response_model=s.TransferenciaResponse
)
def recibir(identity: int, payload: s.RecibirTransferencia, db: Db, user: User):
    return controller.recibir(identity, payload, db, user)


@router.post(
    "/transferencias/{identity}/cancelar", response_model=s.TransferenciaResponse
)
def cancelar(identity: int, db: Db, user: User):
    return controller.cancelar(identity, db, user)
