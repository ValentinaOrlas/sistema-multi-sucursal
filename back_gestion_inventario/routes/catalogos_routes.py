from controllers import catalogos_controller as controller
from core.dependencies import Admin, Db, User
from dtos import schemas as s
from fastapi import APIRouter, Query
from models import (
    CategoriaModel,
    ProductoModel,
    ProveedorModel,
    SucursalesModel,
)

router = APIRouter(tags=["Catálogos"])


def register(
    path,
    model,
    create_schema,
    update_schema,
    response_schema,
    *,
    permitir_creacion=True,
):
    def list_rows(
        db: Db,
        user: User,
        offset: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=200),
    ):
        return controller.list_rows(model, db, user, offset, limit)

    def get_row(identity: int, db: Db, user: User):
        return controller.get_row(model, identity, db, user)

    def create_row(payload: create_schema, db: Db, user: Admin):
        return controller.create_row(model, payload, db, user)

    def update_row(identity: int, payload: update_schema, db: Db, user: Admin):
        return controller.update_row(model, identity, payload, db, user)

    def delete_row(identity: int, db: Db, user: Admin):
        return controller.delete_row(model, identity, db, user)

    for endpoint, suffix, methods, response, status in [
        (list_rows, "", ["GET"], list[response_schema], 200),
        (get_row, "/{identity}", ["GET"], response_schema, 200),
        (create_row, "", ["POST"], response_schema, 201),
        (update_row, "/{identity}", ["PATCH"], response_schema, 200),
        (delete_row, "/{identity}", ["DELETE"], None, 204),
    ]:
        if endpoint is create_row and not permitir_creacion:
            continue
        router.add_api_route(
            "/" + path + suffix,
            endpoint,
            methods=methods,
            response_model=response,
            status_code=status,
            name=f"{path}_{endpoint.__name__}",
        )


register(
    "sucursales",
    SucursalesModel,
    s.SucursalCreate,
    s.SucursalUpdate,
    s.SucursalResponse,
)
register(
    "categorias",
    CategoriaModel,
    s.CategoriaCreate,
    s.CategoriaUpdate,
    s.CategoriaResponse,
)
register(
    "productos",
    ProductoModel,
    s.ProductoCreate,
    s.ProductoUpdate,
    s.ProductoResponse,
    permitir_creacion=False,
)
register(
    "proveedores",
    ProveedorModel,
    s.ProveedorCreate,
    s.ProveedorUpdate,
    s.ProveedorResponse,
)


@router.get("/roles", response_model=list[s.RoleResponse])
def roles(db: Db, user: Admin):
    return controller.roles(db, user)


@router.get("/usuarios", response_model=list[s.UsuarioResponse])
def usuarios(
    db: Db,
    user: Admin,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
):
    return controller.usuarios(db, user, offset, limit)


@router.post("/usuarios", response_model=s.UsuarioResponse, status_code=201)
def crear_usuario(payload: s.UsuarioCreate, db: Db, user: Admin):
    return controller.crear_usuario(payload, db, user)


@router.patch("/usuarios/{identity}", response_model=s.UsuarioResponse)
def editar_usuario(identity: int, payload: s.UsuarioUpdate, db: Db, user: Admin):
    return controller.editar_usuario(identity, payload, db, user)


@router.get("/productos/{identity}/unidades", response_model=list[s.UnidadResponse])
def unidades(identity: int, db: Db, user: User):
    return controller.unidades(identity, db, user)


@router.post(
    "/productos/{identity}/unidades", response_model=s.UnidadResponse, status_code=201
)
def crear_unidad(identity: int, payload: s.UnidadCreate, db: Db, user: Admin):
    return controller.crear_unidad(identity, payload, db, user)


@router.get("/listas-precios", response_model=list[s.ListaResponse])
def listas(db: Db, user: User):
    return controller.listas(db, user)


@router.post("/listas-precios", response_model=s.ListaResponse, status_code=201)
def crear_lista(payload: s.ListaCreate, db: Db, user: Admin):
    return controller.crear_lista(payload, db, user)


@router.get("/listas-precios/{identity}/precios", response_model=list[s.PrecioResponse])
def precios(identity: int, db: Db, user: User):
    return controller.precios(identity, db, user)


@router.put("/listas-precios/{identity}/precios", response_model=s.PrecioResponse)
def guardar_precio(identity: int, payload: s.PrecioCreate, db: Db, user: Admin):
    return controller.guardar_precio(identity, payload, db, user)
