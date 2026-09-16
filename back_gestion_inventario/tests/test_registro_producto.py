"""Aceptación: registro exclusivo del operador con ingreso inicial auditable."""

import os
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal
from threading import Barrier

import pytest
from sqlalchemy import select, func
from conftest import as_user
from conection.conectionDb import getDb
from core.seguridad import Seguridad
from models import (
    ProductoModel,
    InventarioSucursalModel,
    MovimientosInventarioModel,
    UsuarioModel,
    SucursalesModel,
)
from repositories.producto_repository import (
    ProductoRepository,
)


@pytest.fixture
def datos_producto():
    return dict(
        sku="TEC-REG-001",
        nombre="SSD NVMe 1 TB",
        categoria_id=1,
        unidad_medida="unidad",
        stock_minimo="3",
        cantidad_inicial="10",
        costo_unitario="250000.125000",
    )


def sesion(api):
    return contextmanager(api.app.dependency_overrides[getDb])()


def no_hay_registro(api, sku):
    with sesion(api) as db:
        assert (
            db.scalar(select(ProductoModel.id).where(ProductoModel.sku == sku)) is None
        )
        assert db.scalar(select(func.count()).select_from(InventarioSucursalModel)) == 0
        assert (
            db.scalar(select(func.count()).select_from(MovimientosInventarioModel)) == 0
        )


def test_registro_catalogo_stock_y_trazabilidad(api, datos_producto):
    as_user(api, 3)
    antes = datetime.now(timezone.utc)
    response = api.post("/api/productos", json=datos_producto)
    assert response.status_code == 201, response.text
    body = response.json()
    p, i, m = body["producto"], body["inventario"], body["movimiento"]
    assert p["sku"] == datos_producto["sku"]
    assert p["categoria_id"] == 1
    assert i["producto_id"] == m["producto_id"] == p["id"]
    assert i["sucursal_id"] == m["sucursal_id"] == 1
    assert (
        Decimal(i["stock_actual"])
        == Decimal(m["cantidad"])
        == Decimal(m["stock_resultante"])
        == 10
    )
    assert Decimal(i["stock_minimo_local"]) == 3
    assert (
        Decimal(i["costo_promedio_ponderado"])
        == Decimal(m["costo_unitario"])
        == Decimal("250000.125")
    )
    assert m["usuario_id"] == 3
    assert m["tipo_movimiento"] == "INGRESO"
    assert m["motivo"] == "Registro inicial de producto tecnológico"
    fecha = datetime.fromisoformat(m["fecha_movimiento"].replace("Z", "+00:00"))
    assert antes <= fecha <= datetime.now(timezone.utc)
    with sesion(api) as db:
        assert db.get(ProductoModel, p["id"]).stock_minimo_global == 0
        assert db.scalar(select(func.count()).select_from(InventarioSucursalModel)) == 1
        assert (
            db.scalar(
                select(InventarioSucursalModel).where(
                    InventarioSucursalModel.sucursal_id == 2
                )
            )
            is None
        )
        assert db.get(MovimientosInventarioModel, m["id"]).usuario_id == 3


@pytest.mark.parametrize("usuario", [1, 2, 4])
def test_admin_y_gerentes_no_pueden_registrar(api, datos_producto, usuario):
    as_user(api, usuario)
    response = api.post("/api/productos", json=datos_producto)
    assert response.status_code == 403
    assert response.json()["codigo"] == "OPERADOR_REQUERIDO"
    no_hay_registro(api, datos_producto["sku"])


@pytest.mark.parametrize("token", [None, "Bearer invalido", "Basic abc"])
def test_interceptor_rechaza_credenciales_invalidas(api, datos_producto, token):
    api.headers.pop("Authorization", None)
    if token:
        api.headers["Authorization"] = token
    response = api.post("/api/productos", json=datos_producto)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    no_hay_registro(api, datos_producto["sku"])


@pytest.mark.parametrize(
    "campo,valor",
    [
        ("cantidad_inicial", 0),
        ("cantidad_inicial", -1),
        ("cantidad_inicial", "1.0001"),
        ("stock_minimo", -1),
        ("costo_unitario", -1),
        ("costo_unitario", "NaN"),
        ("sku", "   "),
        ("nombre", ""),
        ("unidad_medida", ""),
        ("sucursal_id", 2),
        ("usuario_id", 1),
        ("motivo", "Otro motivo"),
    ],
)
def test_validaciones_y_atributos_protegidos(api, datos_producto, campo, valor):
    as_user(api, 3)
    original_sku = datos_producto["sku"]
    datos_producto[campo] = valor
    response = api.post("/api/productos", json=datos_producto)
    assert response.status_code == 422, response.text
    no_hay_registro(api, original_sku)


def test_categoria_inexistente(api, datos_producto):
    as_user(api, 3)
    datos_producto["categoria_id"] = 999
    response = api.post("/api/productos", json=datos_producto)
    assert response.status_code == 404
    assert response.json()["codigo"] == "CATEGORIA_NO_ENCONTRADA"
    no_hay_registro(api, datos_producto["sku"])


def test_sku_existente_es_error_de_negocio(api, datos_producto):
    as_user(api, 3)
    datos_producto["sku"] = "P1"
    response = api.post("/api/productos", json=datos_producto)
    assert response.status_code == 409
    assert response.json()["codigo"] == "SKU_DUPLICADO"
    with sesion(api) as db:
        assert db.scalar(select(func.count()).select_from(ProductoModel)) == 2
        assert (
            db.scalar(select(func.count()).select_from(MovimientosInventarioModel)) == 0
        )


def test_repetir_peticion_no_duplica_ingreso(api, datos_producto):
    as_user(api, 3)
    assert api.post("/api/productos", json=datos_producto).status_code == 201
    assert api.post("/api/productos", json=datos_producto).status_code == 409
    with sesion(api) as db:
        assert db.scalar(select(func.count()).select_from(InventarioSucursalModel)) == 1
        assert (
            db.scalar(select(func.count()).select_from(MovimientosInventarioModel)) == 1
        )
        assert db.scalar(select(InventarioSucursalModel.stock_actual)) == 10


@pytest.mark.parametrize(
    "cambio", ["usuario_inactivo", "sin_sucursal", "sucursal_inactiva"]
)
def test_contexto_operador_debe_ser_vigente(api, datos_producto, cambio):
    as_user(api, 3)
    with sesion(api) as db:
        if cambio == "usuario_inactivo":
            db.get(UsuarioModel, 3).activo = False
        elif cambio == "sin_sucursal":
            db.get(UsuarioModel, 3).sucursal_id = None
        else:
            db.get(SucursalesModel, 1).activa = False
    response = api.post("/api/productos", json=datos_producto)
    assert response.status_code == (401 if cambio == "usuario_inactivo" else 403)
    no_hay_registro(api, datos_producto["sku"])


def test_unidad_libre_admite_cable_por_metros(api, datos_producto):
    as_user(api, 3)
    datos_producto.update(
        nombre="Cable de red CAT6",
        unidad_medida="metro",
        cantidad_inicial="12.500",
        stock_minimo="2.500",
    )
    response = api.post("/api/productos", json=datos_producto)
    assert response.status_code == 201, response.text
    assert response.json()["producto"]["unidad_medida"] == "metro"
    assert Decimal(response.json()["movimiento"]["cantidad"]) == Decimal("12.5")


def test_fallo_al_guardar_auditoria_revierte_todo(api, datos_producto, monkeypatch):
    as_user(api, 3)
    original = ProductoRepository.insertar_movimiento

    def fallar(self, movimiento):
        original(self, movimiento)
        raise RuntimeError("Fallo simulado antes de confirmar")

    monkeypatch.setattr(ProductoRepository, "insertar_movimiento", fallar)
    with pytest.raises(RuntimeError, match="Fallo simulado"):
        api.post("/api/productos", json=datos_producto)
    no_hay_registro(api, datos_producto["sku"])


def test_swagger_expone_nuevo_contrato_y_autenticacion(api):
    spec = api.get("/openapi.json").json()
    operation = spec["paths"]["/api/productos"]["post"]
    assert operation["requestBody"]["content"]["application/json"]["schema"][
        "$ref"
    ].endswith("RegistrarProductoDto")
    assert operation["security"] == [{"HTTPBearer": []}]


@pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="Requiere PostgreSQL")
def test_sku_unico_en_registros_simultaneos_de_distintas_sucursales(
    api, datos_producto, monkeypatch
):
    with sesion(api) as db:
        db.get(UsuarioModel, 4).rol_id = 3
    barrier = Barrier(2)
    original = ProductoRepository.buscar_por_sku

    def sincronizar(self, sku):
        encontrado = original(self, sku)
        barrier.wait(timeout=10)
        return encontrado

    monkeypatch.setattr(ProductoRepository, "buscar_por_sku", sincronizar)

    def registrar(usuario):
        token = Seguridad.generar_jwt({"sub": str(usuario)})
        return api.post(
            "/api/productos",
            json=datos_producto,
            headers={"Authorization": "Bearer " + token},
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(registrar, [3, 4]))
    assert sorted(r.status_code for r in responses) == [201, 409], [
        r.text for r in responses
    ]
    assert (
        next(r for r in responses if r.status_code == 409).json()["codigo"]
        == "SKU_DUPLICADO"
    )
    with sesion(api) as db:
        assert db.scalar(select(func.count()).select_from(InventarioSucursalModel)) == 1
        assert (
            db.scalar(select(func.count()).select_from(MovimientosInventarioModel)) == 1
        )


def test_sql_parametrizado_trata_comillas_como_datos(api, datos_producto):
    as_user(api, 3)
    datos_producto["sku"] = "TEC-' OR '1'='1"
    datos_producto["nombre"] = "Monitor 27' con base ajustable"
    response = api.post("/api/productos", json=datos_producto)
    assert response.status_code == 201, response.text
    assert response.json()["producto"]["sku"] == datos_producto["sku"]
    assert response.json()["producto"]["nombre"] == datos_producto["nombre"]
    with sesion(api) as db:
        assert db.scalar(select(func.count()).select_from(ProductoModel)) == 3
        assert (
            db.scalar(select(func.count()).select_from(MovimientosInventarioModel)) == 1
        )
    # La búsqueda parametrizada encuentra exactamente ese SKU al repetirlo.
    response = api.post("/api/productos", json=datos_producto)
    assert response.status_code == 409
    assert response.json()["codigo"] == "SKU_DUPLICADO"


def test_descripcion_se_guarda_con_el_registro(api, datos_producto):
    as_user(api, 3)
    datos_producto["descripcion"] = "SSD NVMe PCIe 4.0, 1 TB"
    response = api.post("/api/productos", json=datos_producto)
    assert response.status_code == 201, response.text
    product = response.json()["producto"]
    assert product["descripcion"] == datos_producto["descripcion"]
    assert api.get(f"/api/productos/{product['id']}").json()["descripcion"] == datos_producto["descripcion"]
