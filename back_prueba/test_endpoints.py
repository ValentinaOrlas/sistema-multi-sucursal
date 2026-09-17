"""Integración HTTP contra una copia temporal del esquema actual.

Ejecutar dentro del contenedor de prueba con DB_NAME=test_endpoints_* y
API_TEST_URL apuntando a ese mismo contenedor. Nunca usar una base real.
"""
import json
import os
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import bcrypt
from conection.conectionDb import obtener_conexion

BASE = os.getenv('API_TEST_URL', 'http://127.0.0.1:8000') + '/api'

class EndpointsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.getenv('DB_NAME', '').startswith('test_endpoints_'):
            raise RuntimeError('Estas pruebas requieren una base temporal test_endpoints_*.')
        cls.password = 'PruebaTemporal2026!'
        cls.tag = uuid.uuid4().hex[:10]
        cls.users = {}
        with obtener_conexion() as conn, conn.cursor() as cur:
            cls.branches = []
            for i in range(2):
                cur.execute('INSERT INTO sucursales(nombre,ubicacion,activa) VALUES(%s,%s,TRUE) RETURNING id', (f'QA {cls.tag} {i}', 'Prueba'))
                cls.branches.append(cur.fetchone()[0])
            for role in ('ADMIN_GENERAL','OPERADOR_INVENTARIO','GERENTE_SUCURSAL'):
                cur.execute('INSERT INTO roles(nombre) VALUES(%s) ON CONFLICT(nombre) DO UPDATE SET nombre=EXCLUDED.nombre RETURNING id', (role,))
                role_id = cur.fetchone()[0]
                email = f'{role.lower()}.{cls.tag}@example.com'
                cur.execute('INSERT INTO usuarios(nombre,email,password_hash,rol_id,sucursal_id,activo) VALUES(%s,%s,%s,%s,%s,TRUE) RETURNING id',
                    (role,email,bcrypt.hashpw(cls.password.encode(),bcrypt.gensalt()).decode(),role_id,None if role=='ADMIN_GENERAL' else cls.branches[0]))
                cls.users[role] = {'id':cur.fetchone()[0], 'email':email}
            cur.execute('INSERT INTO categorias(nombre) VALUES(%s) RETURNING id', (f'Tecnología QA {cls.tag}',))
            cls.category = cur.fetchone()[0]
            cur.execute('INSERT INTO proveedores(nombre,tiempo_entrega_promedio_dias) VALUES(%s,2) RETURNING id',(f'Proveedor QA {cls.tag}',))
            cls.supplier = cur.fetchone()[0]
        cls.tokens = {}
        for role, user in cls.users.items():
            status, data = cls.request('POST','/auth/login', {'email':user['email'],'password':cls.password})
            assert status == 200, data
            cls.tokens[role] = data['access_token']

    @classmethod
    def request(cls, method, path, body=None, role=None):
        headers = {'Content-Type':'application/json'}
        if role:
            headers['Authorization'] = 'Bearer ' + cls.tokens[role]
        req = Request(BASE+path, data=json.dumps(body).encode() if body is not None else None, headers=headers, method=method)
        try:
            with urlopen(req, timeout=15) as response:
                return response.status, json.load(response)
        except HTTPError as error:
            return error.code, json.load(error)

    def call(self, method, path, body=None, role='OPERADOR_INVENTARIO', expected=200):
        status, data = self.request(method,path,body,role)
        self.assertEqual(status,expected,data)
        return data

    def product(self, quantity=10, cost=100):
        body = dict(sku='QA-'+uuid.uuid4().hex, nombre='Laptop de prueba',descripcion='Integración',
            categoria_id=self.category,unidad_medida='unidad',cantidad_inicial=quantity,stock_minimo=3,costo_unitario=cost)
        return self.call('POST','/inventario/productos',body,expected=201),body

    def stock(self, product_id):
        return next(i for i in self.call('GET',f'/inventario?sucursal_id={self.branches[0]}') if i['producto_id']==product_id)

    def sale(self, product_id, quantity=1):
        return dict(sucursal_id=self.branches[0], usuario_id=self.users['ADMIN_GENERAL']['id'],
            detalles=[dict(producto_id=product_id,cantidad=quantity,precio_unitario=150,descuento_aplicado=10)])

    def order(self, product_id):
        return self.call('POST','/compras/ordenes',dict(proveedor_id=self.supplier,sucursal_destino_id=self.branches[0],
            plazo_pago_dias=30,detalles=[dict(producto_id=product_id,cantidad=2,precio_unitario=200,descuento=10)]),expected=201)['id']

    def test_01_auth_and_read_routes(self):
        for path in ['/inventario','/categorias','/sucursales','/inventario/productos','/ventas','/compras/ordenes','/listas-precios','/proveedores']:
            self.call('GET',path,role=None,expected=401)
            self.call('GET',path)
        me = self.call('GET','/auth/me')
        self.assertEqual(me['id'],self.users['OPERADOR_INVENTARIO']['id'])
        self.assertNotIn('password_hash',me)
        self.call('POST','/auth/login',dict(email=self.users['ADMIN_GENERAL']['email'],password='incorrecta'),role=None,expected=401)
        self.call('GET',f'/inventario/sucursales/{self.branches[1]}')
        self.call('GET',f'/inventario/movimientos?sucursal_id={self.branches[1]}',expected=403)
        self.call('GET',f'/ventas?sucursal_id={self.branches[1]}',expected=403)

    def test_02_product_crud_audit_and_validation(self):
        p,body = self.product('2.500','10.250000')
        self.assertEqual(Decimal(str(self.stock(p['id'])['stock_actual'])),Decimal('2.500'))
        self.call('POST','/inventario/productos',body,expected=409)
        self.call('POST','/inventario/productos',{**body,'cantidad_inicial':0},expected=422)
        self.call('POST','/inventario/productos',body,role='ADMIN_GENERAL',expected=403)
        changed = {k:body[k] for k in ('sku','nombre','descripcion','categoria_id')}
        changed['nombre'] = 'Laptop actualizada'
        self.call('PATCH',f"/inventario/productos/{p['id']}",changed)
        self.assertEqual(self.call('GET',f"/inventario/productos/{p['id']}")['nombre'],changed['nombre'])
        movements = self.call('GET',f"/inventario/movimientos?producto_id={p['id']}")
        self.assertEqual(len(movements),1)
        self.assertEqual(movements[0]['usuario_id'], self.users['OPERADOR_INVENTARIO']['id'])
        self.assertTrue(movements[0]['fecha_movimiento'])
        self.assertTrue(movements[0]['motivo'])
        self.call('DELETE',f"/inventario/productos/{p['id']}",role='ADMIN_GENERAL',expected=409)
        self.call('POST','/inventario',dict(sucursal_id=self.branches[0],producto_id=p['id'],stock_minimo_local=7),role='GERENTE_SUCURSAL')
        alerts = self.call('GET',f'/inventario/sucursales/{self.branches[0]}/alertas')
        self.assertTrue(any(i['producto_id']==p['id'] for i in alerts))
        with obtener_conexion() as conn, conn.cursor() as cur:
            cur.execute('INSERT INTO productos(sku,nombre,categoria_id,unidad_medida,stock_minimo_global) VALUES(%s,%s,%s,%s,0) RETURNING id',('QA-'+uuid.uuid4().hex,'Sin historial',self.category,'unidad'))
            unused = cur.fetchone()[0]
        self.call('DELETE',f'/inventario/productos/{unused}',role='ADMIN_GENERAL')
        self.call('GET',f'/inventario/productos/{unused}',expected=404)

    def test_03_movements(self):
        p,_ = self.product()
        body = dict(sucursal_id=self.branches[0],producto_id=p['id'],cantidad=2,motivo='Compra: recepción QA',
            tipo_movimiento='INGRESO',costo_unitario=200,usuario_id=self.users['ADMIN_GENERAL']['id'])
        m = self.call('POST','/inventario/movimientos',body,expected=201)
        self.assertEqual(m['usuario_id'],self.users['OPERADOR_INVENTARIO']['id'])
        self.assertAlmostEqual(float(self.stock(p['id'])['costo_promedio_ponderado']),116.666667)
        self.call('POST','/inventario/movimientos',{**body,'sucursal_id':self.branches[1]},expected=403)
        self.call('POST','/inventario/movimientos',body,role='GERENTE_SUCURSAL',expected=403)
        self.call('POST','/inventario/movimientos/retiro',{**body,'cantidad':13},expected=409)
        self.assertEqual(float(self.stock(p['id'])['stock_actual']),12)

    def test_04_orders_receive_and_cancel(self):
        p,_ = self.product()
        order = self.order(p['id'])
        self.assertEqual(self.call('GET',f'/compras/ordenes/{order}')['plazo_pago_dias'],30)
        self.assertTrue(any(o['id']==order for o in self.call('GET',f'/compras/ordenes?producto_id={p["id"]}')))
        with ThreadPoolExecutor(2) as pool:
            results = list(pool.map(lambda _:self.request('POST',f'/compras/ordenes/{order}/recibir',{},'OPERADOR_INVENTARIO'),range(2)))
        self.assertEqual(sorted(r[0] for r in results),[200,409],results)
        self.assertEqual(float(self.stock(p['id'])['stock_actual']),12)
        self.assertAlmostEqual(float(self.stock(p['id'])['costo_promedio_ponderado']),113.333333)
        movement = self.call('GET',f'/inventario/movimientos?producto_id={p["id"]}')[0]
        self.assertEqual(movement['orden_compra_id'],order)
        self.assertEqual(movement['usuario_id'],self.users['OPERADOR_INVENTARIO']['id'])
        cancelled = self.order(p['id'])
        self.call('POST',f'/compras/ordenes/{cancelled}/cancelar',role='GERENTE_SUCURSAL')
        self.call('POST',f'/compras/ordenes/{cancelled}/recibir',expected=409)

    def test_05_sales_atomicity_and_concurrency(self):
        p,_ = self.product()
        body = self.sale(p['id'],7)
        with ThreadPoolExecutor(2) as pool:
            results = list(pool.map(lambda _:self.request('POST','/ventas',body,'OPERADOR_INVENTARIO'),range(2)))
        self.assertEqual(sorted(r[0] for r in results),[201,409],results)
        sale = next(r[1]['comprobante'] for r in results if r[0]==201)
        self.assertEqual(sale['usuario_id'],self.users['OPERADOR_INVENTARIO']['id'])
        self.assertEqual(float(sale['total_venta']),945)
        self.assertEqual(float(self.stock(p['id'])['stock_actual']),3)
        self.call('GET',f'/ventas/{sale["id"]}')
        before = len(self.call('GET','/ventas'))
        second,_ = self.product(1)
        body = self.sale(p['id'],1)
        body['detalles'].append(dict(producto_id=second['id'],cantidad=2,precio_unitario=10))
        self.call('POST','/ventas',body,expected=409)
        self.assertEqual(len(self.call('GET','/ventas')),before)
        self.assertEqual(float(self.stock(p['id'])['stock_actual']),3)
        movements = self.call('GET',f'/inventario/movimientos?producto_id={p["id"]}')
        self.assertEqual(len(movements),2)
        self.assertEqual(movements[0]['venta_id'],sale['id'])

    def test_06_prices_and_supplier_update(self):
        p,_ = self.product()
        with obtener_conexion() as conn, conn.cursor() as cur:
            cur.execute('INSERT INTO listas_precios(nombre) VALUES(%s) RETURNING id',('QA-'+uuid.uuid4().hex,))
            price_list = cur.fetchone()[0]
            cur.execute('INSERT INTO precios_producto(lista_id,producto_id,precio) VALUES(%s,%s,250)',(price_list,p['id']))
        self.call('GET',f'/listas-precios/{price_list}/precios')
        body = self.sale(p['id'])
        body['lista_precio_id'] = price_list
        sale = self.call('POST','/ventas',body,expected=201)['comprobante']
        self.assertEqual(float(sale['total_venta']),225)
        self.call('PUT',f'/proveedores/{self.supplier}',dict(nombre='Proveedor actualizado QA'),role='ADMIN_GENERAL')
        self.call('PUT',f'/proveedores/{self.supplier}',dict(nombre='No permitido'),expected=403)

if __name__ == '__main__':
    unittest.main(verbosity=2)
