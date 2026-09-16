import os
import subprocess
import sys
import uuid
import pytest
from sqlalchemy.engine import make_url
from pathlib import Path
from sqlalchemy import create_engine, inspect, text

ROOT = Path(__file__).resolve().parents[1]


def run(url, *args):
    env = {**os.environ, "DATABASE_URL": url}
    result = subprocess.run(
        [sys.executable, *args], cwd=ROOT, env=env, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return result


@pytest.fixture
def migration_url(tmp_path):
    source = os.getenv("TEST_DATABASE_URL")
    if not source:
        yield "sqlite:///" + str(tmp_path / "migration.db")
        return
    name = "migration_" + uuid.uuid4().hex
    control = create_engine(source, isolation_level="AUTOCOMMIT")
    with control.connect() as db:
        db.execute(text(f'CREATE DATABASE "{name}"'))
    try:
        yield make_url(source).set(database=name).render_as_string(hide_password=False)
    finally:
        with control.connect() as db:
            db.execute(text(f'DROP DATABASE "{name}" WITH (FORCE)'))
        control.dispose()


def test_fresh_migration_matches_models(migration_url):
    url = migration_url
    run(url, "-m", "core.migrate")
    run(url, "-m", "alembic", "check")
    assert (
        len(inspect(create_engine(url)).get_table_names()) == 18
    )  # 17 domain tables + alembic


def test_adopt_populated_legacy_preserves_data(migration_url):
    url = migration_url
    run(url, "-m", "alembic", "upgrade", "0001")
    engine = create_engine(url)
    with engine.begin() as db:
        db.execute(
            text(
                "INSERT INTO sucursales (id,nombre,ubicacion,activa) VALUES (1,'Centro','A',TRUE)"
            )
        )
        db.execute(text("INSERT INTO categorias (id,nombre) VALUES (1,'General')"))
        db.execute(
            text(
                "INSERT INTO productos (id,sku,nombre,categoria_id,unidad_medida,stock_minimo_global) VALUES (1,'P1','Producto',1,'unidad',0)"
            )
        )
        db.execute(
            text(
                "INSERT INTO inventario_sucursal (id,sucursal_id,producto_id,stock_actual,stock_minimo_local,costo_promedio_ponderado) VALUES (1,1,1,10,2,7.5)"
            )
        )
        db.execute(
            text(
                "INSERT INTO movimientos_inventario (id,sucursal_id,producto_id,cantidad,tipo_movimiento,motivo,stock_resultante) VALUES (1,1,1,10,'INGRESO','Inicial',10)"
            )
        )
        db.execute(text("DROP TABLE alembic_version"))
    run(url, "-m", "core.migrate")
    with engine.connect() as db:
        row = db.execute(
            text(
                "SELECT stock_actual,costo_promedio_ponderado FROM inventario_sucursal"
            )
        ).one()
        assert tuple(row) == (10, 7.5)
        assert db.scalar(text("SELECT usuario_id FROM movimientos_inventario")) is None
        assert db.scalar(text("SELECT count(*) FROM movimientos_inventario")) == 1
    run(url, "-m", "alembic", "check")
    engine.dispose()


def test_unknown_legacy_schema_is_not_modified(migration_url):
    url = migration_url
    engine = create_engine(url)
    with engine.begin() as db:
        db.execute(text("CREATE TABLE importante (id INTEGER PRIMARY KEY)"))
        db.execute(text("INSERT INTO importante VALUES (1)"))
    result = subprocess.run(
        [sys.executable, "-m", "core.migrate"],
        cwd=ROOT,
        env={**os.environ, "DATABASE_URL": url},
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert inspect(engine).get_table_names() == ["importante"]
    engine.dispose()


def test_role_migration_preserves_users_and_merges_names(migration_url):
    url = migration_url
    run(url, "-m", "alembic", "upgrade", "0002")
    engine = create_engine(url)
    with engine.begin() as db:
        db.execute(
            text(
                "INSERT INTO roles (id,nombre) VALUES (10,'ADMIN'),(11,'ADMIN_GENERAL'),(20,'GERENTE'),(30,'OPERADOR')"
            )
        )
        db.execute(
            text(
                "INSERT INTO usuarios (id,nombre,email,password_hash,rol_id,activo) VALUES (50,'Anterior','anterior@example.com','hash-conservado',10,TRUE),(51,'Actual','actual@example.com','otro-hash',11,TRUE)"
            )
        )
    run(url, "-m", "core.migrate")
    with engine.connect() as db:
        assert set(db.scalars(text("SELECT nombre FROM roles"))) == {
            "ADMIN_GENERAL",
            "GERENTE_SUCURSAL",
            "OPERADOR_INVENTARIO",
        }
        assert db.scalar(text("SELECT count(*) FROM usuarios")) == 2
        assert list(db.scalars(text("SELECT rol_id FROM usuarios ORDER BY id"))) == [
            11,
            11,
        ]
        assert (
            db.scalar(text("SELECT password_hash FROM usuarios WHERE id=50"))
            == "hash-conservado"
        )
    engine.dispose()
