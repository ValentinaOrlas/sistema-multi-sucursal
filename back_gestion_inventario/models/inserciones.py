"""Datos iniciales de un inventario de artículos tecnológicos.

Ejecutar desde back_gestion_inventario:
    python -m models.inserciones --sucursal-id 1

La sucursal debe existir y estar activa. SEED_PASSWORD permite proporcionar
la contraseña inicial; si no está definida, se solicita sin mostrarla.
Importar este módulo no ejecuta inserciones ni crea tablas.
"""

import argparse
import getpass
import json
import os
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from conection.conectionDb import SessionLocal
from core.seguridad import Seguridad
from models.categoriasModel import CategoriaModel
from models.productosModel import ProductoModel
from models.rolesModel import RoleModel
from models.sucursalesModel import SucursalesModel
from models.usuariosModel import UsuarioModel


ROLES = (
    (
        "ADMIN_GENERAL",
        "Gestiona configuración, usuarios, sucursales y tiene visibilidad total del sistema.",
    ),
    (
        "GERENTE_SUCURSAL",
        "Supervisa operaciones de su sucursal, aprueba transferencias y consulta reportes.",
    ),
    (
        "OPERADOR_INVENTARIO",
        "Realiza ingresos, retiros, solicita transferencias y registra ventas/compras.",
    ),
)

CATEGORIAS = (
    ("Computadores", "Equipos portátiles y computadores de escritorio."),
    ("Periféricos", "Dispositivos de entrada y salida para computadores."),
    ("Almacenamiento", "Unidades internas y externas para guardar información."),
    ("Redes", "Equipos para conectividad y comunicación de datos."),
    ("Componentes", "Piezas para ensamblar, ampliar o reparar computadores."),
    ("Accesorios", "Complementos y adaptadores para equipos tecnológicos."),
)

# SKU, nombre, categoría, descripción y stock mínimo en unidades.
PRODUCTOS = (
    (
        "TEC-COM-001",
        "Portátil de 15 pulgadas",
        "Computadores",
        "Portátil con 16 GB de RAM y SSD de 512 GB.",
        3,
    ),
    (
        "TEC-COM-002",
        "Computador de escritorio",
        "Computadores",
        "Equipo de escritorio con 16 GB de RAM y SSD de 1 TB.",
        2,
    ),
    (
        "TEC-PER-001",
        "Teclado mecánico USB",
        "Periféricos",
        "Teclado en español con conexión USB.",
        10,
    ),
    (
        "TEC-PER-002",
        "Mouse inalámbrico",
        "Periféricos",
        "Mouse óptico con receptor USB.",
        15,
    ),
    (
        "TEC-ALM-001",
        "SSD NVMe de 1 TB",
        "Almacenamiento",
        "Unidad de estado sólido M.2 NVMe de 1 TB.",
        8,
    ),
    (
        "TEC-ALM-002",
        "Disco externo de 2 TB",
        "Almacenamiento",
        "Disco portátil de 2 TB con conexión USB.",
        5,
    ),
    (
        "TEC-RED-001",
        "Router Wi-Fi de doble banda",
        "Redes",
        "Router para redes inalámbricas de 2.4 y 5 GHz.",
        5,
    ),
    (
        "TEC-RED-002",
        "Switch de 8 puertos",
        "Redes",
        "Switch de escritorio con ocho puertos Gigabit Ethernet.",
        4,
    ),
    (
        "TEC-CMP-001",
        "Memoria RAM DDR4 de 16 GB",
        "Componentes",
        "Módulo de memoria para computador de escritorio.",
        10,
    ),
    (
        "TEC-CMP-002",
        "Fuente de poder de 650 W",
        "Componentes",
        "Fuente de alimentación para computador de escritorio.",
        4,
    ),
    (
        "TEC-ACC-001",
        "Adaptador USB-C a HDMI",
        "Accesorios",
        "Adaptador para conectar un equipo USB-C a una pantalla HDMI.",
        12,
    ),
    (
        "TEC-ACC-002",
        "Base para portátil",
        "Accesorios",
        "Soporte ajustable para computador portátil.",
        8,
    ),
)

USUARIOS = (
    ("Administrador de tecnología", "admin.tecnologia@example.com", "ADMIN_GENERAL"),
    ("Gerente de tecnología", "gerente.tecnologia@example.com", "GERENTE_SUCURSAL"),
    (
        "Operador de tecnología",
        "operador.tecnologia@example.com",
        "OPERADOR_INVENTARIO",
    ),
)


def insertar_roles(db: Session) -> tuple[dict[str, RoleModel], int]:
    """Busca roles por nombre e inserta únicamente los que faltan."""
    roles = {}
    creados = 0
    for nombre, descripcion in ROLES:
        rol = db.scalar(select(RoleModel).where(RoleModel.nombre == nombre))
        if rol is None:
            rol = RoleModel(nombre=nombre, descripcion=descripcion)
            db.add(rol)
            db.flush()
            creados += 1
        roles[nombre] = rol
    return roles, creados


def insertar_datos(db: Session, sucursal_id: int, password: str) -> dict:
    """Carga las cuatro tablas; el llamador controla el commit o rollback.

    Las claves naturales son nombre de rol/categoría, SKU y email. Los registros
    existentes se conservan, incluidos sus nombres, contraseñas y asignaciones.
    Los IDs se obtienen de la base: no se asume que comiencen en 1.
    """
    sucursal = db.get(SucursalesModel, sucursal_id)
    if sucursal is None or not sucursal.activa:
        raise ValueError("La sucursal indicada debe existir y estar activa.")
    if len(password) < 10 or len(password.encode("utf-8")) > 72:
        raise ValueError(
            "La contraseña debe tener al menos 10 caracteres y como máximo 72 bytes UTF-8."
        )

    roles, creados_roles = insertar_roles(db)
    resumen = {
        "roles": {"creados": creados_roles, "existentes": len(ROLES) - creados_roles},
        "categorias": {"creados": 0, "existentes": 0},
        "productos": {"creados": 0, "existentes": 0},
        "usuarios": {"creados": 0, "existentes": 0},
    }
    categorias = {}
    for nombre, descripcion in CATEGORIAS:
        categoria = db.scalar(
            select(CategoriaModel).where(CategoriaModel.nombre == nombre)
        )
        if categoria is None:
            categoria = CategoriaModel(nombre=nombre, descripcion=descripcion)
            db.add(categoria)
            db.flush()
            resumen["categorias"]["creados"] += 1
        else:
            resumen["categorias"]["existentes"] += 1
        categorias[nombre] = categoria

    for sku, nombre, categoria, descripcion, minimo in PRODUCTOS:
        existente = db.scalar(select(ProductoModel).where(ProductoModel.sku == sku))
        if existente is not None:
            resumen["productos"]["existentes"] += 1
            continue
        db.add(
            ProductoModel(
                sku=sku,
                nombre=nombre,
                descripcion=descripcion,
                categoria_id=categorias[categoria].id,
                unidad_medida="unidad",
                stock_minimo_global=Decimal(minimo),
            )
        )
        resumen["productos"]["creados"] += 1

    for nombre, email, rol in USUARIOS:
        existente = db.scalar(select(UsuarioModel).where(UsuarioModel.email == email))
        if existente is not None:
            resumen["usuarios"]["existentes"] += 1
            continue
        db.add(
            UsuarioModel(
                nombre=nombre,
                email=email,
                password_hash=Seguridad.encriptarContrasena(password),
                rol_id=roles[rol].id,
                sucursal_id=None if rol == "ADMIN_GENERAL" else sucursal.id,
                activo=True,
            )
        )
        resumen["usuarios"]["creados"] += 1
    db.flush()
    return resumen


def main():
    parser = argparse.ArgumentParser(
        description="Insertar datos iniciales de artículos tecnológicos."
    )
    parser.add_argument(
        "--sucursal-id",
        type=int,
        required=True,
        help="Sucursal existente y activa para el gerente y el operador.",
    )
    args = parser.parse_args()
    password = os.getenv("SEED_PASSWORD") or getpass.getpass(
        "Contraseña inicial de los usuarios de ejemplo: "
    )
    try:
        with SessionLocal.begin() as db:
            resumen = insertar_datos(db, args.sucursal_id, password)
    except ValueError as exc:
        parser.exit(1, f"No se insertaron datos: {exc}\n")
    # Solo se informa éxito después de confirmar la transacción.
    print(json.dumps(resumen, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
