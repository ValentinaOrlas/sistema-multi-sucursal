import os
import sys
import uuid
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "test-secret-only-0123456789-0123456789"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from conection.conectionDb import getDb
from core.seguridad import Seguridad
from main import app
from models import (
    Base,
    RoleModel,
    SucursalesModel,
    UsuarioModel,
    CategoriaModel,
    ProductoModel,
    ProveedorModel,
)


@pytest.fixture
def api():
    pg_url = os.getenv("TEST_DATABASE_URL")
    schema = "test_" + uuid.uuid4().hex
    if pg_url:
        from sqlalchemy import text

        control = create_engine(pg_url)
        with control.begin() as conn:
            conn.execute(text(f'CREATE SCHEMA "{schema}"'))
        engine = create_engine(
            pg_url, connect_args={"options": f"-c search_path={schema} -c timezone=UTC"}
        )
    else:
        engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )

        @event.listens_for(engine, "connect")
        def fk(conn, _):
            conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
    with factory.begin() as db:
        db.add_all(
            [
                RoleModel(id=1, nombre="ADMIN_GENERAL"),
                RoleModel(id=2, nombre="GERENTE_SUCURSAL"),
                RoleModel(id=3, nombre="OPERADOR_INVENTARIO"),
                SucursalesModel(id=1, nombre="Centro", ubicacion="A"),
                SucursalesModel(id=2, nombre="Norte", ubicacion="B"),
                CategoriaModel(id=1, nombre="General"),
                ProveedorModel(id=1, nombre="Proveedor"),
            ]
        )
        db.flush()
        db.add_all(
            [
                UsuarioModel(
                    id=1,
                    nombre="Admin",
                    email="admin@example.com",
                    password_hash=Seguridad.encriptarContrasena("Password123!"),
                    rol_id=1,
                ),
                UsuarioModel(
                    id=2,
                    nombre="Gerente",
                    email="gerente@example.com",
                    password_hash="unused",
                    rol_id=2,
                    sucursal_id=1,
                ),
                UsuarioModel(
                    id=3,
                    nombre="Operador",
                    email="operador@example.com",
                    password_hash="unused",
                    rol_id=3,
                    sucursal_id=1,
                ),
                UsuarioModel(
                    id=4,
                    nombre="Destino",
                    email="destino@example.com",
                    password_hash="unused",
                    rol_id=2,
                    sucursal_id=2,
                ),
                ProductoModel(
                    id=1,
                    sku="P1",
                    nombre="Producto 1",
                    categoria_id=1,
                    unidad_medida="unidad",
                ),
                ProductoModel(
                    id=2,
                    sku="P2",
                    nombre="Producto 2",
                    categoria_id=1,
                    unidad_medida="kg",
                ),
            ]
        )
    if pg_url:
        # Explicit fixture IDs do not advance PostgreSQL sequences.
        with engine.begin() as conn:
            for table in (
                "roles",
                "sucursales",
                "usuarios",
                "categorias",
                "productos",
                "proveedores",
            ):
                conn.execute(
                    text(
                        f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), (SELECT max(id) FROM {table}))"
                    )
                )

    def session():
        with factory() as db:
            try:
                yield db
                db.commit()
            except Exception:
                db.rollback()
                raise

    app.dependency_overrides[getDb] = session
    with TestClient(app) as client:
        client.headers["Authorization"] = "Bearer " + Seguridad.generar_jwt(
            {"sub": "1"}
        )
        yield client
    app.dependency_overrides.clear()
    engine.dispose()
    if pg_url:
        with control.begin() as conn:
            conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        control.dispose()


def as_user(api, identity):
    api.headers["Authorization"] = "Bearer " + Seguridad.generar_jwt(
        {"sub": str(identity)}
    )
