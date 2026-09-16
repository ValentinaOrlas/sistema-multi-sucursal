"""SQL explícito del registro inicial, ejecutado en la sesión de SQLAlchemy.

Los valores se envían como parámetros. Ningún método confirma la transacción;
el producto, el inventario y el movimiento se confirman o revierten juntos.
"""

from exceptions.producto_exceptions import SkuDuplicado
from sqlalchemy import DateTime, Numeric, bindparam, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


class ProductoRepository:
    def __init__(self, db: Session):
        self.db = db

    def buscar_usuario(self, usuario_id: int) -> dict | None:
        consulta = text("""
            SELECT u.id, u.activo, u.sucursal_id, r.nombre AS rol_nombre
            FROM usuarios AS u
            INNER JOIN roles AS r ON r.id = u.rol_id
            WHERE u.id = :usuario_id
        """)
        fila = self.db.execute(consulta, {"usuario_id": usuario_id}).mappings().first()
        return dict(fila) if fila is not None else None

    def bloquear_sucursal(self, sucursal_id: int) -> dict | None:
        sql = """
            SELECT id, nombre, activa
            FROM sucursales
            WHERE id = :sucursal_id
        """

        if self.db.get_bind().dialect.name == "postgresql":
            sql += " FOR UPDATE"
        fila = (
            self.db.execute(text(sql), {"sucursal_id": sucursal_id}).mappings().first()
        )
        return dict(fila) if fila is not None else None

    def buscar_categoria(self, categoria_id: int) -> dict | None:
        sql = """
            SELECT id, nombre
            FROM categorias
            WHERE id = :categoria_id
        """
        if self.db.get_bind().dialect.name == "postgresql":
            sql += " FOR SHARE"
        fila = (
            self.db.execute(text(sql), {"categoria_id": categoria_id})
            .mappings()
            .first()
        )
        return dict(fila) if fila is not None else None

    def buscar_por_sku(self, sku: str) -> dict | None:
        consulta = text("""
            SELECT id, sku
            FROM productos
            WHERE sku = :sku
        """)
        fila = self.db.execute(consulta, {"sku": sku}).mappings().first()
        return dict(fila) if fila is not None else None

    def insertar_producto(self, producto: dict) -> dict:
        consulta = text("""
            INSERT INTO productos (
                sku, nombre, descripcion, categoria_id, unidad_medida, stock_minimo_global
            )
            VALUES (
                :sku, :nombre, :descripcion, :categoria_id, :unidad_medida, 0
            )
            RETURNING id, sku, nombre, descripcion, categoria_id, unidad_medida
        """)
        try:
            fila = self.db.execute(consulta, producto).mappings().one()
        except IntegrityError as exc:
            # UNIQUE resuelve también la carrera entre dos sucursales que
            # intenten registrar el mismo SKU después de la consulta previa.
            diagnostico = getattr(exc.orig, "diag", None)
            restriccion = getattr(diagnostico, "constraint_name", None)
            if restriccion in {
                "ix_productos_sku",
                "productos_sku_key",
            } or "UNIQUE constraint failed: productos.sku" in str(exc.orig):
                raise SkuDuplicado() from exc
            raise
        return dict(fila)

    def insertar_inventario(self, inventario: dict) -> dict:
        consulta = (
            text("""
            INSERT INTO inventario_sucursal (
                producto_id, sucursal_id, stock_actual, stock_minimo_local,
                costo_promedio_ponderado
            )
            VALUES (
                :producto_id, :sucursal_id, :stock_actual, :stock_minimo_local,
                :costo_promedio_ponderado
            )
            RETURNING id, producto_id, sucursal_id, stock_actual,
                      stock_minimo_local, costo_promedio_ponderado
        """)
            .bindparams(
                bindparam("stock_actual", type_=Numeric(14, 3)),
                bindparam("stock_minimo_local", type_=Numeric(14, 3)),
                bindparam("costo_promedio_ponderado", type_=Numeric(18, 6)),
            )
            .columns(
                stock_actual=Numeric(14, 3),
                stock_minimo_local=Numeric(14, 3),
                costo_promedio_ponderado=Numeric(18, 6),
            )
        )
        # Los tipos convierten parámetros/resultados Decimal también en SQLite.
        fila = self.db.execute(consulta, inventario).mappings().one()
        return dict(fila)

    def insertar_movimiento(self, movimiento: dict) -> dict:
        consulta = (
            text("""
            INSERT INTO movimientos_inventario (
                producto_id, sucursal_id, usuario_id, tipo_movimiento, motivo,
                cantidad, stock_resultante, costo_unitario, fecha_movimiento
            )
            VALUES (
                :producto_id, :sucursal_id, :usuario_id, :tipo_movimiento, :motivo,
                :cantidad, :stock_resultante, :costo_unitario, :fecha_movimiento
            )
            RETURNING id, producto_id, sucursal_id, usuario_id, tipo_movimiento,
                      motivo, cantidad, stock_resultante, costo_unitario,
                      fecha_movimiento
        """)
            .bindparams(
                bindparam("cantidad", type_=Numeric(14, 3)),
                bindparam("stock_resultante", type_=Numeric(14, 3)),
                bindparam("costo_unitario", type_=Numeric(18, 6)),
                bindparam("fecha_movimiento", type_=DateTime()),
            )
            .columns(
                cantidad=Numeric(14, 3),
                stock_resultante=Numeric(14, 3),
                costo_unitario=Numeric(18, 6),
                fecha_movimiento=DateTime(),
            )
        )
        fila = self.db.execute(consulta, movimiento).mappings().one()
        return dict(fila)
