"""Nombres de roles definidos para el inventario multisucursal."""

from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

CAMBIOS = (
    ("ADMIN", "ADMIN_GENERAL"),
    ("GERENTE", "GERENTE_SUCURSAL"),
    ("OPERADOR", "OPERADOR_INVENTARIO"),
)


def upgrade():
    db = op.get_bind()
    roles = sa.table(
        "roles", sa.column("id", sa.Integer), sa.column("nombre", sa.String)
    )
    usuarios = sa.table("usuarios", sa.column("rol_id", sa.Integer))
    for anterior, nuevo in CAMBIOS:
        anterior_id = db.scalar(sa.select(roles.c.id).where(roles.c.nombre == anterior))
        if anterior_id is None:
            continue
        nuevo_id = db.scalar(sa.select(roles.c.id).where(roles.c.nombre == nuevo))
        if nuevo_id is None:
            db.execute(
                roles.update().where(roles.c.id == anterior_id).values(nombre=nuevo)
            )
        else:
            # Si se cargó el catálogo nuevo antes de migrar, conserva el rol
            # canónico y sus usuarios; reasigna las referencias del nombre viejo.
            db.execute(
                usuarios.update()
                .where(usuarios.c.rol_id == anterior_id)
                .values(rol_id=nuevo_id)
            )
            db.execute(roles.delete().where(roles.c.id == anterior_id))


def downgrade():
    raise RuntimeError(
        "La unificación de roles no se revierte automáticamente: sus asignaciones ya pueden haber cambiado."
    )
