from contextlib import contextmanager
from sqlalchemy import select, func
import pytest

from conection.conectionDb import getDb
from core.seguridad import Seguridad
from models import (
    CategoriaModel,
    ProductoModel,
    UsuarioModel,
    RoleModel,
    SucursalesModel,
    InventarioSucursalModel,
)
from models.inserciones import insertar_datos, USUARIOS


def session(api):
    return contextmanager(api.app.dependency_overrides[getDb])()


def count(db, model):
    return db.scalar(select(func.count()).select_from(model))


def test_seed_technology_relations_and_passwords(api):
    with session(api) as db:
        result = insertar_datos(db, sucursal_id=2, password="Tecnologia2026!")
        assert result["categorias"]["creados"] == 6
        assert result["productos"]["creados"] == 12
        assert result["usuarios"]["creados"] == 3
        assert {r.nombre for r in db.scalars(select(RoleModel))} == {
            "ADMIN_GENERAL",
            "GERENTE_SUCURSAL",
            "OPERADOR_INVENTARIO",
        }
        for _, email, expected_role in USUARIOS:
            user = db.scalar(select(UsuarioModel).where(UsuarioModel.email == email))
            assert user.rol.nombre == expected_role
            assert user.sucursal_id == (None if expected_role == "ADMIN_GENERAL" else 2)
            assert user.password_hash != "Tecnologia2026!"
            assert Seguridad.verificar_contrasena("Tecnologia2026!", user.password_hash)
        products = db.scalars(
            select(ProductoModel).where(ProductoModel.sku.like("TEC-%"))
        ).all()
        assert len(products) == 12
        assert {p.categoria.nombre for p in products} == {
            "Computadores",
            "Periféricos",
            "Almacenamiento",
            "Redes",
            "Componentes",
            "Accesorios",
        }
        assert count(db, SucursalesModel) == 2
        assert count(db, InventarioSucursalModel) == 0


def test_seed_can_repeat_and_preserves_edits(api):
    with session(api) as db:
        insertar_datos(db, 1, "Tecnologia2026!")
        product = db.scalar(
            select(ProductoModel).where(ProductoModel.sku == "TEC-COM-001")
        )
        product.nombre = "Nombre editado por el usuario"
        user = db.scalar(
            select(UsuarioModel).where(UsuarioModel.email == USUARIOS[0][1])
        )
        original_hash = user.password_hash
    with session(api) as db:
        result = insertar_datos(db, 2, "OtraPassword2026!")
        assert all(row["creados"] == 0 for row in result.values())
        assert (
            count(db, CategoriaModel) == 7
        )  # La categoría General previa también se conserva.
        assert count(db, ProductoModel) == 14
        assert count(db, UsuarioModel) == 7
        assert (
            db.scalar(
                select(ProductoModel).where(ProductoModel.sku == "TEC-COM-001")
            ).nombre
            == "Nombre editado por el usuario"
        )
        assert (
            db.scalar(
                select(UsuarioModel).where(UsuarioModel.email == USUARIOS[0][1])
            ).password_hash
            == original_hash
        )
        manager = db.scalar(
            select(UsuarioModel).where(UsuarioModel.email == USUARIOS[1][1])
        )
        assert manager.sucursal_id == 1


def test_invalid_branch_does_not_insert(api):
    with pytest.raises(ValueError, match="sucursal"):
        with session(api) as db:
            insertar_datos(db, 999, "Tecnologia2026!")
    with session(api) as db:
        assert count(db, CategoriaModel) == 1
        assert count(db, ProductoModel) == 2


def test_seed_rolls_back_on_failure(api, monkeypatch):
    def fail(_):
        raise RuntimeError("Fallo simulado al preparar usuario")

    monkeypatch.setattr(Seguridad, "encriptarContrasena", fail)
    with pytest.raises(RuntimeError):
        with session(api) as db:
            insertar_datos(db, 1, "Tecnologia2026!")
    with session(api) as db:
        assert count(db, CategoriaModel) == 1
        assert count(db, ProductoModel) == 2
        assert count(db, UsuarioModel) == 4


def test_seeded_roles_work_in_api(api):
    with session(api) as db:
        insertar_datos(db, 1, "Tecnologia2026!")
    for _, email, role in USUARIOS:
        login = api.post(
            "/api/auth/login", json={"email": email, "password": "Tecnologia2026!"}
        )
        assert login.status_code == 200
        api.headers["Authorization"] = "Bearer " + login.json()["access_token"]
        assert api.get("/api/auth/me").json()["rol"]["nombre"] == role
        assert api.get("/api/productos").status_code == 200
        assert api.get("/api/usuarios").status_code == (
            200 if role == "ADMIN_GENERAL" else 403
        )
