"""Solo PostgreSQL: SQLite no implementa SELECT FOR UPDATE."""

import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import pytest
from test_operaciones import ingreso, stock, transfer

pytestmark = pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"), reason="Requiere PostgreSQL aislado"
)


def test_two_sales_cannot_oversell(api):
    ingreso(api, qty=5)
    barrier = Barrier(2)

    def sell():
        barrier.wait(timeout=10)
        return api.post(
            "/api/ventas",
            json={
                "sucursal_id": 1,
                "detalles": [{"producto_id": 1, "cantidad": 4, "precio_unitario": 10}],
            },
        ).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(lambda _: sell(), range(2)))
    assert sorted(statuses) == [201, 409]
    assert stock(api) == 1
    assert len(api.get("/api/ventas").json()) == 1


def test_two_receipts_cannot_duplicate_stock(api):
    ingreso(api, qty=10)
    row, data = transfer(api)
    barrier = Barrier(2)

    def receive():
        barrier.wait(timeout=10)
        return api.post(
            f"/api/transferencias/{row['id']}/recibir", json=data
        ).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(lambda _: receive(), range(2)))
    assert sorted(statuses) == [200, 409]
    assert stock(api, 2) == 6


def test_concurrent_first_ingress_creates_one_stock_row(api):
    barrier = Barrier(2)

    def receive():
        barrier.wait(timeout=10)
        return api.post(
            "/api/inventario/movimientos",
            json={
                "sucursal_id": 1,
                "producto_id": 1,
                "cantidad": 5,
                "tipo_movimiento": "INGRESO",
                "motivo": "Inicial",
                "costo_unitario": 2,
            },
        ).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(lambda _: receive(), range(2)))
    assert statuses == [201, 201]
    assert stock(api) == 10
    assert len(api.get("/api/inventario").json()) == 1
