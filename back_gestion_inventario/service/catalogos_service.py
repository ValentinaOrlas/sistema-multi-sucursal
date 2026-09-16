from core.seguridad import Seguridad
from dtos import schemas as s
from fastapi import HTTPException
from models import (
    ListaPrecioModel,
    PrecioProductoModel,
    ProductoModel,
    RoleModel,
    SucursalesModel,
    UnidadProductoModel,
    UsuarioModel,
)
from repositories import inventario_repository as repo

from service.inventario_service import require


def apply_patch(obj, payload):
    for key, value in payload.model_dump(exclude_unset=True).items():
        if value is None and not obj.__table__.columns[key].nullable:
            raise HTTPException(422, f"{key} no puede ser nulo")
        setattr(obj, key, value)


def roles(db, user):
    return repo.rows(
        db,
        RoleModel,
        "nombre IN ('ADMIN_GENERAL','GERENTE_SUCURSAL','OPERADOR_INVENTARIO')",
    )


def usuarios(
    db,
    user,
    offset: int = 0,
    limit: int = 100,
):
    return repo.rows(db, UsuarioModel, offset=offset, limit=limit)


def validate_user(db, role_id, branch_id):
    role = require(db, RoleModel, role_id)
    if role.nombre not in {"ADMIN_GENERAL", "GERENTE_SUCURSAL", "OPERADOR_INVENTARIO"}:
        raise HTTPException(422, "Rol no admitido")
    if role.nombre != "ADMIN_GENERAL" and branch_id is None:
        raise HTTPException(422, "Gerente y operador requieren sucursal")
    if branch_id is not None and not require(db, SucursalesModel, branch_id).activa:
        raise HTTPException(422, "La sucursal debe estar activa")


def crear_usuario(payload: s.UsuarioCreate, db, user):
    validate_user(db, payload.rol_id, payload.sucursal_id)
    data = payload.model_dump(exclude={"password"})
    data["email"] = str(payload.email).lower()
    obj = UsuarioModel(
        **data, password_hash=Seguridad.encriptarContrasena(payload.password)
    )
    repo.save(db, obj)
    return obj


def editar_usuario(identity: int, payload: s.UsuarioUpdate, db, user):
    require(db, UsuarioModel, identity)
    obj = repo.get(db, UsuarioModel, identity, lock=True)
    data = payload.model_dump(exclude_unset=True)
    if identity == user.id and any(k in data for k in ("rol_id", "activo")):
        raise HTTPException(409, "No puedes cambiar tu propio rol o estado")
    password = data.pop("password", None)
    if password:
        obj.password_hash = Seguridad.encriptarContrasena(password)
    if "email" in data and data["email"] is not None:
        data["email"] = str(data["email"]).lower()
    for key, value in data.items():
        if value is None and not obj.__table__.columns[key].nullable:
            raise HTTPException(422, f"{key} no puede ser nulo")
        setattr(obj, key, value)
    validate_user(db, obj.rol_id, obj.sucursal_id)
    repo.save(db, obj)
    return obj


def unidades(identity: int, db, user):
    require(db, ProductoModel, identity)
    return repo.rows(
        db, UnidadProductoModel, "producto_id = :identity", {"identity": identity}
    )


def crear_unidad(identity: int, payload: s.UnidadCreate, db, user):
    require(db, ProductoModel, identity)
    obj = UnidadProductoModel(producto_id=identity, **payload.model_dump())
    repo.save(db, obj)
    return obj


def listas(db, user):
    return repo.rows(db, ListaPrecioModel)


def crear_lista(payload: s.ListaCreate, db, user):
    obj = ListaPrecioModel(**payload.model_dump())
    repo.save(db, obj)
    return obj


def precios(identity: int, db, user):
    require(db, ListaPrecioModel, identity)
    return repo.rows(
        db, PrecioProductoModel, "lista_id = :identity", {"identity": identity}
    )


def guardar_precio(identity: int, payload: s.PrecioCreate, db, user):
    require(db, ListaPrecioModel, identity)
    require(db, ProductoModel, payload.producto_id)
    # Serialize first insert/update for the same price list.
    repo.get(db, ListaPrecioModel, identity, lock=True)
    obj = repo.find(
        db, PrecioProductoModel, lista_id=identity, producto_id=payload.producto_id
    )
    if obj is None:
        obj = PrecioProductoModel(lista_id=identity, **payload.model_dump())
    else:
        obj.precio = payload.precio
    return repo.save(db, obj)


def list_rows(model, db, user, offset, limit):
    return repo.rows(db, model, offset=offset, limit=limit)


def get_row(model, identity, db, user):
    return require(db, model, identity)


def create_row(model, payload, db, user):
    return repo.save(db, model(**payload.model_dump()))


def update_row(model, identity, payload, db, user):
    require(db, model, identity)
    obj = repo.get(db, model, identity, lock=True)
    apply_patch(obj, payload)
    return repo.save(db, obj)


def delete_row(model, identity, db, user):
    if model is SucursalesModel and repo.find(db, UsuarioModel, sucursal_id=identity):
        raise HTTPException(
            409, "La sucursal tiene usuarios asignados; puedes desactivarla"
        )
    repo.delete(db, require(db, model, identity))
