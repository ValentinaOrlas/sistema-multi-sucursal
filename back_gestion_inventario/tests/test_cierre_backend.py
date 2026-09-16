"""Regresiones de los flujos completos y consultas SQL parametrizadas."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from conftest import as_user
from test_operaciones import ingreso, post, stock


def test_catalog_sql_literals_and_updates(api):
    name = "Monitor ' OLED; DROP TABLE productos; --"
    category = post(api, '/categorias', {'nombre': name})
    assert api.get(f"/api/categorias/{category['id']}").json()['nombre'] == name
    response = api.patch(f"/api/categorias/{category['id']}", json={'descripcion': 'Pantallas'})
    assert response.status_code == 200
    assert response.json()['nombre'] == name
    assert response.json()['descripcion'] == 'Pantallas'
    assert api.get('/api/productos').status_code == 200
    assert api.delete(f"/api/categorias/{category['id']}").status_code == 204
    assert api.get(f"/api/categorias/{category['id']}").status_code == 404


def test_purchase_filters_and_receipt_audit(api):
    first = post(api, '/compras', {'proveedor_id': 1, 'sucursal_destino_id': 1,
        'plazo_pago_dias': 30, 'detalles': [{'producto_id': 1, 'cantidad': 3, 'precio_unitario': 12, 'descuento': 10}]})
    post(api, '/compras', {'proveedor_id': 1, 'sucursal_destino_id': 1,
        'detalles': [{'producto_id': 2, 'cantidad': 2, 'precio_unitario': 5}]})
    result = api.get('/api/compras', params={'producto_id': 1, 'proveedor_id': 1}).json()
    assert [x['id'] for x in result] == [first['id']]
    as_user(api, 3)
    assert api.post(f"/api/compras/{first['id']}/recibir").status_code == 200
    assert api.post(f"/api/compras/{first['id']}/recibir").status_code == 409
    assert stock(api) == 3
    movement = api.get('/api/inventario/movimientos').json()[0]
    assert movement['usuario_id'] == 3
    assert movement['orden_compra_id'] == first['id']
    assert movement['fecha_movimiento'] and movement['motivo']
    assert Decimal(movement['costo_unitario']) == Decimal('10.8')
    assert api.get('/api/compras', params={'sucursal_id': 2}).status_code == 403


def test_logistics_sorting_and_branch_reports(api):
    ingreso(api, 20)
    for priority, price, hours in [('BAJA', 2, 48), ('ALTA', 10, 12)]:
        row = post(api, '/transferencias', {'sucursal_origen_id': 1, 'sucursal_destino_id': 2,
            'prioridad': priority, 'detalles': [{'producto_id': 1, 'cantidad': 2}]})
        details = {'detalles': [{'detalle_id': row['detalles'][0]['id'], 'cantidad': 2}]}
        post(api, f"/transferencias/{row['id']}/preparar", details, 200)
        post(api, f"/transferencias/{row['id']}/despachar", {'transportista': 'Transporte',
            'ruta': 'Centro-Norte', 'costo_envio': price,
            'fecha_estimada_llegada': (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()}, 200)
    assert api.get('/api/reportes/logistica').json()['transferencias'][0]['prioridad'] == 'ALTA'
    assert api.get('/api/reportes/logistica?ordenar_por=costo').json()['transferencias'][0]['prioridad'] == 'BAJA'
    assert api.get('/api/reportes/logistica?ordenar_por=tiempo').json()['transferencias'][0]['prioridad'] == 'ALTA'
    assert api.get('/api/reportes/logistica?ordenar_por=invalido').status_code == 422
    as_user(api, 3)
    for path in ['/dashboard', '/analisis/demanda', '/reportes/logistica']:
        assert api.get('/api' + path, params={'sucursal_id': 2}).status_code == 403
        assert api.get('/api' + path).status_code == 200
    assert api.get('/api/dashboard').json()['comparativa_sucursales'] == []


def test_price_upsert_and_user_role_refresh(api):
    price_list = post(api, '/listas-precios', {'nombre': 'Tecnología'})
    url = f"/api/listas-precios/{price_list['id']}/precios"
    first = api.put(url, json={'producto_id': 1, 'precio': 20})
    second = api.put(url, json={'producto_id': 1, 'precio': 25})
    assert first.status_code == second.status_code == 200
    assert first.json()['id'] == second.json()['id']
    assert len(api.get(url).json()) == 1
    assert Decimal(api.get(url).json()[0]['precio']) == 25
    response = api.patch('/api/usuarios/3', json={'rol_id': 2})
    assert response.status_code == 200
    assert response.json()['rol']['nombre'] == 'GERENTE_SUCURSAL'
    as_user(api, 3)
    assert api.get('/api/auth/me').json()['rol']['nombre'] == 'GERENTE_SUCURSAL'
