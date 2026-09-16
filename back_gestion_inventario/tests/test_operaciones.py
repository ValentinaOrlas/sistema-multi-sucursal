from datetime import datetime, timedelta, timezone
from decimal import Decimal
from conftest import as_user


def post(api, path, data=None, status=201):
    response = (
        api.post("/api" + path, json=data)
        if data is not None
        else api.post("/api" + path)
    )
    assert response.status_code == status, response.text
    return response.json()


def ingreso(api, qty=10, price=5, product=1, branch=1):
    return post(
        api,
        "/inventario/movimientos",
        {
            "sucursal_id": branch,
            "producto_id": product,
            "cantidad": qty,
            "tipo_movimiento": "INGRESO",
            "motivo": "Inicial",
            "costo_unitario": price,
        },
    )


def stock(api, branch=1, product=1):
    rows = api.get(
        "/api/inventario", params={"sucursal_id": branch, "producto_id": product}
    ).json()
    return Decimal(rows[0]["stock_actual"]) if rows else Decimal(0)


def sale(api, details):
    return api.post("/api/ventas", json={"sucursal_id": 1, "detalles": details})


def transfer(api, qty=6):
    row = post(
        api,
        "/transferencias",
        {
            "sucursal_origen_id": 1,
            "sucursal_destino_id": 2,
            "detalles": [{"producto_id": 1, "cantidad": qty}],
        },
    )
    data = {"detalles": [{"detalle_id": row["detalles"][0]["id"], "cantidad": qty}]}
    post(api, f"/transferencias/{row['id']}/preparar", data, 200)
    post(
        api,
        f"/transferencias/{row['id']}/despachar",
        {
            "transportista": "Transporte",
            "ruta": "Centro-Norte",
            "fecha_estimada_llegada": (
                datetime.now(timezone.utc) + timedelta(days=1)
            ).isoformat(),
        },
        200,
    )
    return row, data


def test_auth_and_no_hash_exposure(api):
    api.headers.pop("Authorization")
    assert api.get("/api/productos").status_code == 401
    response = post(
        api,
        "/auth/login",
        {"email": "admin@example.com", "password": "Password123!"},
        200,
    )
    api.headers["Authorization"] = "Bearer " + response["access_token"]
    me = api.get("/api/auth/me")
    assert me.status_code == 200
    assert "password_hash" not in me.text
    assert (
        api.post(
            "/api/auth/login", json={"email": "admin@example.com", "password": "wrong"}
        ).status_code
        == 401
    )


def test_permissions_and_responsible(api):
    as_user(api, 3)
    assert (
        api.post(
            "/api/categorias",
            json={"nombre": "Componentes tecnológicos"},
        ).status_code
        == 403
    )
    response = api.post(
        "/api/inventario/movimientos",
        json={
            "sucursal_id": 2,
            "producto_id": 1,
            "cantidad": 1,
            "tipo_movimiento": "INGRESO",
            "motivo": "test",
            "costo_unitario": 1,
        },
    )
    assert response.status_code == 403
    row = ingreso(api)
    assert row["usuario_id"] == 3
    assert api.get("/api/inventario", params={"sucursal_id": 2}).status_code == 200
    assert api.get("/api/dashboard", params={"sucursal_id": 2}).status_code == 403


def test_sale_atomic_rollback(api):
    ingreso(api)
    response = sale(
        api,
        [
            {"producto_id": 1, "cantidad": 2, "precio_unitario": 10},
            {"producto_id": 2, "cantidad": 1, "precio_unitario": 10},
        ],
    )
    assert response.status_code == 409
    assert stock(api) == 10
    assert api.get("/api/ventas").json() == []
    assert len(api.get("/api/inventario/movimientos").json()) == 1


def test_sale_total_discount_and_no_oversell(api):
    ingreso(api)
    response = sale(
        api,
        [
            {
                "producto_id": 1,
                "cantidad": 3,
                "precio_unitario": 10,
                "descuento_aplicado": 10,
            }
        ],
    )
    assert response.status_code == 201, response.text
    assert Decimal(response.json()["total_venta"]) == 27
    assert stock(api) == 7
    assert (
        sale(
            api, [{"producto_id": 1, "cantidad": 8, "precio_unitario": 10}]
        ).status_code
        == 409
    )
    assert stock(api) == 7


def test_purchase_average_and_double_receive(api):
    ingreso(api, 10, 5)
    order = post(
        api,
        "/compras",
        {
            "proveedor_id": 1,
            "sucursal_destino_id": 1,
            "plazo_pago_dias": 30,
            "detalles": [{"producto_id": 1, "cantidad": 10, "precio_unitario": 15}],
        },
    )
    assert stock(api) == 10
    post(api, f"/compras/{order['id']}/recibir", status=200)
    row = api.get("/api/inventario").json()[0]
    assert Decimal(row["stock_actual"]) == 20
    assert Decimal(row["costo_promedio_ponderado"]) == 10
    assert api.post(f"/api/compras/{order['id']}/recibir").status_code == 409
    assert stock(api) == 20


def test_partial_transfer_and_audit(api):
    ingreso(api, 10, 5)
    row, data = transfer(api)
    assert stock(api) == 4
    assert stock(api, 2) == 0
    data["detalles"][0]["cantidad"] = 4
    data["tratamiento_faltante"] = "RECLAMACION"
    received = post(api, f"/transferencias/{row['id']}/recibir", data, 200)
    assert received["estado"] == "CON_FALTANTES"
    assert Decimal(received["detalles"][0]["faltantes"]) == 2
    assert stock(api, 2) == 4
    target = api.get("/api/inventario", params={"sucursal_id": 2}).json()[0]
    assert Decimal(target["costo_promedio_ponderado"]) == 5
    assert (
        api.post(f"/api/transferencias/{row['id']}/recibir", json=data).status_code
        == 409
    )
    assert stock(api, 2) == 4
    assert api.get("/api/reportes/logistica").json()["rutas"][0]["recibidos"] == 1


def test_transfer_invalid_reception_rollback(api):
    ingreso(api)
    row, data = transfer(api)
    data["detalles"][0]["cantidad"] = 7
    assert (
        api.post(f"/api/transferencias/{row['id']}/recibir", json=data).status_code
        == 422
    )
    assert stock(api, 2) == 0
    data["detalles"][0]["cantidad"] = 5
    assert (
        api.post(f"/api/transferencias/{row['id']}/recibir", json=data).status_code
        == 422
    )
    assert stock(api, 2) == 0
    assert api.get(f"/api/transferencias/{row['id']}").json()["estado"] == "EN_TRANSITO"


def test_dispatch_revalidates_stock(api):
    ingreso(api, 10)
    row = post(
        api,
        "/transferencias",
        {
            "sucursal_origen_id": 1,
            "sucursal_destino_id": 2,
            "detalles": [{"producto_id": 1, "cantidad": 10}],
        },
    )
    post(
        api,
        f"/transferencias/{row['id']}/preparar",
        {"detalles": [{"detalle_id": row["detalles"][0]["id"], "cantidad": 10}]},
        200,
    )
    assert (
        sale(
            api, [{"producto_id": 1, "cantidad": 1, "precio_unitario": 10}]
        ).status_code
        == 201
    )
    response = api.post(
        f"/api/transferencias/{row['id']}/despachar",
        json={
            "transportista": "X",
            "ruta": "A-B",
            "fecha_estimada_llegada": (
                datetime.now(timezone.utc) + timedelta(days=1)
            ).isoformat(),
        },
    )
    assert response.status_code == 409
    assert stock(api) == 9
    assert api.get(f"/api/transferencias/{row['id']}").json()["estado"] == "PREPARADA"


def test_units_fractional_and_prices(api):
    unit = post(api, "/productos/1/unidades", {"nombre": "caja", "factor": 12})
    post(
        api,
        "/inventario/movimientos",
        {
            "sucursal_id": 1,
            "producto_id": 1,
            "cantidad": 2,
            "unidad_id": unit["id"],
            "tipo_movimiento": "INGRESO",
            "motivo": "Cajas",
            "costo_unitario": 60,
        },
    )
    assert stock(api) == 24
    response = sale(
        api,
        [
            {
                "producto_id": 1,
                "cantidad": 1,
                "unidad_id": unit["id"],
                "precio_unitario": 120,
            }
        ],
    )
    assert response.status_code == 201, response.text
    assert Decimal(response.json()["total_venta"]) == 120
    assert stock(api) == 12
    ingreso(api, qty="0.750", price=4, product=2)
    assert stock(api, product=2) == Decimal(".750")


def test_price_list_and_foreign_unit(api):
    ingreso(api)
    price_list = post(api, "/listas-precios", {"nombre": "Mayorista"})
    response = api.put(
        f"/api/listas-precios/{price_list['id']}/precios",
        json={"producto_id": 1, "precio": 8},
    )
    assert response.status_code == 200
    sold = post(
        api,
        "/ventas",
        {
            "sucursal_id": 1,
            "lista_precio_id": price_list["id"],
            "detalles": [{"producto_id": 1, "cantidad": 2}],
        },
    )
    assert Decimal(sold["total_venta"]) == 16
    unit = post(api, "/productos/2/unidades", {"nombre": "bolsa", "factor": 2})
    assert (
        sale(
            api,
            [
                {
                    "producto_id": 1,
                    "cantidad": 1,
                    "precio_unitario": 10,
                    "unidad_id": unit["id"],
                }
            ],
        ).status_code
        == 422
    )


def test_validation_and_referenced_delete(api):
    ingreso(api)
    assert api.delete("/api/productos/1").status_code == 409
    assert sale(api, []).status_code == 422
    assert (
        sale(
            api,
            [
                {
                    "producto_id": 1,
                    "cantidad": 1,
                    "precio_unitario": 2,
                    "descuento_aplicado": 101,
                }
            ],
        ).status_code
        == 422
    )
    assert (
        sale(
            api, [{"producto_id": 1, "cantidad": 1, "precio_unitario": 2}] * 2
        ).status_code
        == 422
    )
    assert api.patch("/api/productos/1", json={"nombre": None}).status_code == 422
    assert api.get("/api/productos/1").json()["nombre"] == "Producto 1"


def test_dashboard_demand_and_alert(api):
    ingreso(api, 10)
    sale(api, [{"producto_id": 1, "cantidad": 4, "precio_unitario": 10}])
    response = api.get("/api/dashboard")
    assert response.status_code == 200, response.text
    data = response.json()
    assert Decimal(str(data["ventas_mensuales"][0]["importe"])) == 40
    assert Decimal(str(data["demanda"][0]["demanda_estimada_30_dias"])) == 4
    post(
        api,
        "/inventario",
        {"sucursal_id": 1, "producto_id": 1, "stock_minimo_local": 8},
    )
    assert len(api.get("/api/inventario/alertas").json()) == 1


def test_operator_cannot_approve_transfer(api):
    ingreso(api)
    row = post(
        api,
        "/transferencias",
        {
            "sucursal_origen_id": 1,
            "sucursal_destino_id": 2,
            "detalles": [{"producto_id": 1, "cantidad": 1}],
        },
    )
    as_user(api, 3)
    assert (
        api.post(
            f"/api/transferencias/{row['id']}/preparar",
            json={
                "detalles": [{"detalle_id": row["detalles"][0]["id"], "cantidad": 1}]
            },
        ).status_code
        == 403
    )


def test_user_management_and_deactivation(api):
    user = post(
        api,
        "/usuarios",
        {
            "nombre": "Nuevo",
            "email": "new@example.com",
            "password": "Secret12345!",
            "rol_id": 3,
            "sucursal_id": 1,
        },
    )
    assert "password" not in user
    assert (
        api.patch(f"/api/usuarios/{user['id']}", json={"activo": False}).status_code
        == 200
    )
    as_user(api, user["id"])
    assert api.get("/api/productos").status_code == 401
