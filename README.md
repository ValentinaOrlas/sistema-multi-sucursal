# sistema-multi-sucursal

## Backend actual (`back_prueba`)

El frontend usa `http://localhost:8000/api`; Docker inicia `back_prueba/main.py`
con `uvicorn`, sin ejecutar migraciones ni inserciones automáticas.

```bash
docker compose up -d --build
```

Rutas usadas por el frontend:

- `POST /api/auth/login`, `GET /api/auth/me`.
- `GET/POST /api/inventario/productos`, `GET/PATCH/DELETE /api/inventario/productos/{id}`.
- `GET/POST /api/categorias`, `GET /api/sucursales`.
- `GET/POST /api/inventario`, `GET/POST /api/inventario/movimientos`.
- `GET /api/inventario/sucursales/{id}/alertas`.
- `GET/POST /api/compras/ordenes`, `GET /api/compras/ordenes/{id}` y
  `POST /api/compras/ordenes/{id}/recibir` o `/cancelar`.
- `GET/POST /api/ventas`, `GET /api/ventas/{id}`.
- `GET /api/listas-precios`, `GET /api/listas-precios/{id}/precios`.
- `GET/POST /api/proveedores`, `PUT /api/proveedores/{id}`.

Se requiere Bearer token salvo para el login. El responsable se obtiene del
usuario autenticado; enviar otro `usuario_id` no cambia la autoría.
El registro de productos exige cantidad inicial positiva, costo unitario y
stock mínimo local. Solo el operador puede crear productos y movimientos manuales.
Compras y ventas guardan stock y movimientos en una única transacción.

**Esquema:** esta integración usa las columnas ya existentes en el volumen de
PostgreSQL: auditoría de movimientos (`usuario_id`, `costo_unitario`, `venta_id`,
`orden_compra_id`), `plazo_pago_dias`, cantidades decimales y tablas de precios.
El archivo original `back_prueba/database/database.sql` no contiene todas estas
ampliaciones y no reproduce por sí solo la base actual. No se modificó ni se
aplicó ese archivo; una instalación desde cero requiere revisar su esquema.

**Pruebas:** `back_prueba/test_endpoints.py` ejecuta seis pruebas de integración
HTTP. Requiere un servidor conectado a una copia temporal del esquema actual,
con nombre `test_endpoints_*`. El script crea datos de prueba únicamente en esa
base y rechaza ejecutarse si `DB_NAME` no tiene ese prefijo. `API_TEST_URL` debe
apuntar al servidor de prueba (por defecto `http://127.0.0.1:8000`).
