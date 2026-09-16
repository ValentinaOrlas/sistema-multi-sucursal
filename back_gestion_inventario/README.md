# Backend del sistema de inventario multisucursal

API FastAPI + SQLAlchemy 2 + PostgreSQL. La lógica de inventario está en el servidor y cada petición de escritura es una transacción.

## Arranque con Docker Compose

Desde la raíz del repositorio:

```bash
docker compose up --build
```

El backend aplica migraciones, carga roles y crea el administrador inicial si no existe. Conserva el volumen `pgdata` existente.

- Documentación interactiva: http://localhost:8000/docs
- Estado: http://localhost:8000/health
- API: `/api`
- Administrador local predeterminado: `admin@example.com`
- Contraseña local predeterminada: `InventarioLocal2026!`

`ADMIN_EMAIL` y `ADMIN_PASSWORD` permiten cambiar esas credenciales al crear el usuario. No cambian la contraseña de un usuario existente. Los valores predeterminados de Compose son para desarrollo local.

En Swagger: ejecuta `POST /api/auth/login`, copia `access_token` y pégalo en **Authorize**. El formulario de HTTP Bearer espera el token sin el prefijo `Bearer`.

## Ejecución sin Docker

Python 3.11 o posterior:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL='postgresql://usuario:password@localhost:5432/multi_sucursal'
export SECRET_KEY='una-clave-de-desarrollo-con-al-menos-32-caracteres'
export ADMIN_EMAIL='admin@example.com'
export ADMIN_PASSWORD='InventarioLocal2026!'
python -m core.migrate
python -m core.bootstrap
uvicorn main:app --reload
```

Sin `DATABASE_URL` se usa SQLite local para exploración. PostgreSQL es necesario para garantizar los bloqueos concurrentes. Las fechas se almacenan y los informes se agrupan en UTC; los despachos requieren una fecha ISO 8601 con zona horaria.

## Inserciones iniciales: artículos tecnológicos

El archivo `models/inserciones.py` carga **3 roles, 6 categorías, 12 productos y
3 usuarios de ejemplo**. Los productos se relacionan con sus categorías y los
usuarios con los roles `ADMIN_GENERAL`, `GERENTE_SUCURSAL` y `OPERADOR_INVENTARIO`.

Desde `back_gestion_inventario`, con `DATABASE_URL` configurada:

```bash
python -m core.migrate
python -m models.inserciones --sucursal-id 1
```

Sustituye `1` por el ID de una sucursal existente y activa. Se necesita para
asignar al gerente y al operador; el administrador general no tiene sucursal.
La carga no crea sucursales ni modifica existencias.

El comando solicita una contraseña inicial sin mostrarla. También admite
`SEED_PASSWORD` en el entorno para una ejecución automatizada. Cada contraseña
se almacena con bcrypt. Usuarios de ejemplo:

| Correo | Rol |
|---|---|
| `admin.tecnologia@example.com` | `ADMIN_GENERAL` |
| `gerente.tecnologia@example.com` | `GERENTE_SUCURSAL` |
| `operador.tecnologia@example.com` | `OPERADOR_INVENTARIO` |

Se usan nombre, SKU y correo para detectar datos existentes. Repetir la carga
no duplica registros ni sobrescribe ediciones, contraseñas o asignaciones
previas. Toda la carga se confirma en una transacción y devuelve un resumen
por tabla. Si falla, se revierte.

La migración `0003` actualiza los nombres anteriores de los roles conservando
los usuarios. Si ya existen ambos nombres, unifica las referencias en el rol
nuevo. La carga de ejemplos es manual: arrancar la API no la ejecuta.

## Primera historia: registrar producto tecnológico

Implementada directamente en las carpetas de la arquitectura acordada.
`POST /api/productos` es exclusivo de `OPERADOR_INVENTARIO`: recibe SKU, nombre,
categoría, unidad de medida, cantidad inicial, costo unitario y stock mínimo local.
Guarda producto, inventario de la sucursal del operador y movimiento inicial auditable
en una sola transacción. El rol ADMIN_GENERAL no puede ejecutar este registro.

Los repositorios de la API usan SQL explícito parametrizado con `text()` y `Session.execute()`.
Contrato, flujo, archivos y errores: `docs/historias/HU01_registro_producto.md`.

## Funciones implementadas

| Módulo | Rutas principales |
|---|---|
| Sesión | `POST /api/auth/login`, `GET /api/auth/me` |
| Catálogos | CRUD de `/api/sucursales`, `/api/categorias`, `/api/productos`, `/api/proveedores` |
| Usuarios | Listar, crear y modificar `/api/usuarios`; consulta de `/api/roles` |
| Unidades | Listar y crear `/api/productos/{id}/unidades` |
| Precios | `/api/listas-precios` y `/api/listas-precios/{id}/precios` |
| Inventario | `/api/inventario`, `/api/inventario/movimientos`, `/api/inventario/alertas` |
| Compras | `/api/compras`, `/{id}/recibir`, `/{id}/cancelar` |
| Ventas | Crear, listar y consultar `/api/ventas` |
| Transferencias | `/api/transferencias`, `/{id}/preparar`, `/{id}/despachar`, `/{id}/recibir`, `/{id}/cancelar` |
| Análisis | `/api/dashboard`, `/api/analisis/demanda`, `/api/reportes/logistica` |

Swagger expone los cuerpos y respuestas exactos. Las listas de operaciones y catálogos admiten `offset` y `limit` (máximo 200). El historial de compras permite filtrar por proveedor y producto.

## Permisos

Responsabilidades definidas para cada actor:

| Rol | Responsabilidades |
|---|---|
| `ADMIN_GENERAL` | Gestiona configuración, usuarios, sucursales y tiene visibilidad total del sistema. |
| `GERENTE_SUCURSAL` | Supervisa operaciones de su sucursal, aprueba transferencias y consulta reportes. |
| `OPERADOR_INVENTARIO` | Realiza ingresos, retiros, solicita transferencias y registra ventas/compras. |

Reglas de acceso implementadas:

- Todos pueden consultar inventarios de otras sucursales. El acceso a ventas, movimientos y reportes se restringe a la propia sucursal salvo ADMIN_GENERAL.
- Una solicitud se crea desde el destino. La preparación requiere gerente del origen. El despacho descuenta del origen; la recepción incrementa el destino.
- Las responsabilidades se toman del token validado contra el usuario actual en la base. La API no acepta un `usuario_id` suministrado por el cliente para atribuir operaciones.

## Recorrido mínimo

1. Iniciar sesión.
2. Como administrador, crear sucursales, categorías tecnológicas, proveedor y un usuario operador.
3. Iniciar sesión como operador y registrar el producto con `POST /api/productos`, indicando cantidad inicial, costo y mínimo local.
4. Crear una compra con `proveedor_id`, `sucursal_destino_id` y `detalles` (producto, cantidad, precio).
5. Confirmar la recepción: aumenta existencias y recalcula el costo promedio.
6. Crear una venta en esa sucursal: valida stock, descuenta existencias y registra su movimiento.
7. Solicitar, preparar, despachar y recibir una transferencia.
8. Consultar dashboard, alertas y movimientos.

Ejemplo de compra:

```json
{
  "proveedor_id": 1,
  "sucursal_destino_id": 1,
  "plazo_pago_dias": 30,
  "detalles": [
    {"producto_id": 1, "cantidad": 10, "precio_unitario": 5000, "descuento": 5}
  ]
}
```

Ejemplo de venta:

```json
{
  "sucursal_id": 1,
  "detalles": [
    {"producto_id": 1, "cantidad": 2, "precio_unitario": 7000, "descuento_aplicado": 0}
  ]
}
```

## Reglas de negocio

- Cantidades con tres decimales. Precios normalizados y costos con seis decimales; total de venta con dos, redondeo `ROUND_HALF_UP` por línea.
- Los descuentos son porcentajes entre 0 y 100.
- `unidad_medida` es la unidad base. Una unidad adicional tiene un `factor`: caja de 12 → factor 12. El cliente puede enviar `unidad_id`; los registros quedan normalizados a la unidad base. No se permite cambiar retrospectivamente la unidad base desde PATCH.
- El precio manual corresponde a la unidad indicada en la petición. Los precios de listas corresponden siempre a la unidad base. No se puede combinar lista con precio manual.
- Un ingreso manual requiere costo. Una salida usa el costo promedio actual. Una transferencia lleva el costo registrado al despachar, no el precio de venta.
- Preparar una transferencia no reserva existencias; el despacho vuelve a validar disponibilidad. Si el stock cambió, responde 409 y permite cancelar la preparación o reponer existencias.
- La recepción de transferencia es final: puede ser completa o parcial. Los faltantes exigen `REENVIO`, `AJUSTE` o `RECLAMACION`. Esa elección registra el tratamiento; un reenvío se realiza mediante una nueva transferencia.
- Repetir una recepción o despacho confirmado devuelve 409. Crear una venta nuevamente crea otra venta: esa ruta no tiene clave de idempotencia.
- Ventas y documentos confirmados no se eliminan por API. Las eliminaciones de catálogos referenciados se rechazan para conservar el historial.
- El dashboard incluye ventas mensuales, mínimos, transferencias y comparativa administrativa. La funcionalidad adicional es una estimación de demanda por promedio móvil; no supone un modelo de aprendizaje automático. La rotación usa una aproximación con stock inicial y final.

## Migraciones y datos existentes

`core.migrate` distingue bases nuevas, bases ya versionadas y el esquema original de 14 tablas. Antes de adoptar este último comprueba sus tablas y columnas. Un esquema diferente detiene el arranque para revisarlo.

La migración conserva stock y movimientos. Los responsables y referencias históricos desconocidos permanecen nulos; los nuevos campos de costo histórico y plazo se inicializan en cero. No se atribuyen acciones antiguas a usuarios inventados. Las transferencias históricas abiertas requieren reconciliación antes de la adopción. Los datos que violen las nuevas restricciones deben corregirse antes de migrar.

La reversión de cantidades decimales a enteros no se automatiza: perdería información. Para entornos con datos reales, conserva un respaldo antes de actualizar. `alembic check` comprueba que el esquema y los modelos coinciden.

## Pruebas

```bash
pip install -r requirements-dev.txt
pytest -q
```

Las pruebas generales usan SQLite temporal. Para ejecutar también las pruebas de concurrencia con PostgreSQL:

```bash
TEST_DATABASE_URL='postgresql://usuario:password@localhost:5432/base_pruebas' pytest -q
```

El usuario de prueba debe poder crear esquemas y bases temporales. Cada prueba PostgreSQL crea un esquema aleatorio y lo elimina al terminar. Las pruebas de migración usan bases temporales en el motor seleccionado. No apuntar las pruebas a producción.

Se comprueban autenticación, aislamiento entre sucursales, descuentos, rollback, costo promedio, unidades, listas de precios, transferencias, conservación de datos y concurrencia. Docker Compose debe verificarse también en un entorno que permita ejecutar contenedores.

## Organización

- `routes/`: routers HTTP.
- `controllers/`: coordinación de servicios.
- `repositories/`: SQL parametrizado.
- `middlewares/`: interceptores.
- `exceptions/`: errores personalizados.
- `dtos/`: contratos de entrada y respuesta; `producto_dto.py` contiene HU01 y `schemas.py` los otros casos de uso.
- `service/`: servicios de negocio de inventario y documentos.
- `models/`: tablas y restricciones.
- `core/`: seguridad, permisos, migración y carga inicial.
- `migrations/`: esquema original congelado y actualizaciones.
- `tests/`: pruebas de integración y concurrencia.

Decisiones y flujos: `docs/arquitectura.md`. Evidencia de trabajo asistido: `docs/uso_ia.md`.

## Cierre funcional del backend

La lógica de todos los módulos HTTP está en `service`; las rutas delegan en
`controllers` y las consultas se ejecutan en `repositories` con SQL parametrizado.
Los modelos siguen definiendo tablas y relaciones. El repositorio compartido
admite exclusivamente tablas y columnas de los modelos conocidos. Las entidades
no se adjuntan a la sesión: guardar requiere una llamada explícita a `save`.
Las migraciones y la carga inicial son comandos administrativos independientes.

`GET /api/reportes/logistica?ordenar_por=prioridad` ordena los envíos por prioridad
(alta primero); también admite `costo` y `tiempo`, en orden ascendente.
El esquema no cambia con esta reorganización. Las pruebas usan bases temporales.
Docker Compose debe comprobarse en el entorno de despliegue.
