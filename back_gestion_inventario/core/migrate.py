"""Adopta solo el esquema original reconocido y aplica migraciones sin borrar datos."""

from pathlib import Path
import ast
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text
from conection.conectionDb import engine

ROOT = Path(__file__).resolve().parents[1]


def legacy_columns():
    tree = ast.parse(
        (ROOT / "migrations/versions/0001_esquema_original.py").read_text()
    )
    result = {}
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "create_table"
        ):
            result[node.args[0].value] = {
                arg.args[0].value
                for arg in node.args[1:]
                if isinstance(arg, ast.Call)
                and isinstance(arg.func, ast.Attribute)
                and arg.func.attr == "Column"
            }
    return result


def migrate():
    config = Config(str(ROOT / "alembic.ini"))
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    if tables and "alembic_version" not in tables:
        expected = legacy_columns()
        if tables != set(expected) or any(
            {c["name"] for c in inspector.get_columns(t)} != cols
            for t, cols in expected.items()
        ):
            raise RuntimeError(
                "Esquema existente distinto del original. Se requiere una migración revisada; no se modificó la base."
            )
        # Existing transfers lack the historical cost snapshot. Never dispatch or
        # receive them with an invented zero cost after adopting this schema.
        with engine.connect() as connection:
            pending = connection.scalar(
                text(
                    "SELECT count(*) FROM transferencias WHERE estado NOT IN ('RECIBIDA','CON_FALTANTES','CANCELADA')"
                )
            )
        if pending:
            raise RuntimeError(
                "Hay transferencias históricas abiertas. Reconcilia su estado y costo antes de migrar."
            )
        command.stamp(config, "0001")
    command.upgrade(config, "head")


if __name__ == "__main__":
    migrate()
