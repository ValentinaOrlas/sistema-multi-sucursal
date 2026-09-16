# HU01 · Registrar un producto tecnológico

**Como operador de inventario, quiero registrar un nuevo producto tecnológico indicando su SKU, nombre, categoría y stock mínimo, para habilitar su control dentro del catálogo de la sucursal.**

## Decisiones confirmadas

- Solo el rol `OPERADOR_INVENTARIO` registra productos mediante esta operación.
- El SKU es único en todo el sistema. Se conserva la restricción existente de la base.
- La cantidad inicial debe ser mayor que cero y pertenece a la sucursal del operador autenticado.
- El mínimo es local: se guarda en `inventario_sucursal.stock_minimo_local`.
- Se captura el costo unitario inicial, no negativo, que establece el primer costo promedio.
- La unidad de medida es obligatoria y de texto libre (por ejemplo, `unidad`, `kit` o `metro`).
- El servidor registra el motivo `Registro inicial de producto tecnológico` y la fecha UTC.
- La categoría debe existir. Su catálogo tecnológico se administra por separado.

## Petición

`POST /api/productos`, con `Authorization: Bearer <token_del_operador>`.

```json
{
  "sku": "TEC-SSD-001",
  "nombre": "SSD NVMe 1 TB",
  "categoria_id": 1,
  "stock_minimo": 3,
  "unidad_medida": "unidad",
  "cantidad_inicial": 10,
  "costo_unitario": 250000
}
```

`categoria_id` debe ser un ID existente. No enviar `usuario_id`, `sucursal_id`, fecha o motivo: se calculan a partir de la sesión y del servidor. Esos campos se rechazan si aparecen en la petición.

Cantidades y mínimos admiten hasta tres decimales; costos admiten hasta seis, de acuerdo con las columnas existentes. El SKU y los textos se recortan en sus extremos; no se cambian mayúsculas/minúsculas ni el esquema de unicidad existente.

## Resultado

HTTP **201**, con tres objetos:

- `producto`: ID, SKU, nombre, categoría y unidad de medida.
- `inventario`: sucursal, stock inicial, mínimo local y costo promedio.
- `movimiento`: ingreso inicial, cantidad, stock resultante, costo, responsable, fecha y motivo.

Los tres registros pertenecen a una única transacción. Si falla cualquier inserción o la confirmación, no se conserva una creación parcial. Repetir el SKU devuelve 409 y no vuelve a incrementar las existencias.

## Arquitectura implementada

Los archivos están directamente en las siguientes carpetas:

| Carpeta | Archivo | Función |
|---|---|---|
| `conection` | `sesion.py` | Reutiliza `getDb`; confirma la transacción antes de responder. |
| `middlewares` | `autenticacion_middleware.py` | Intercepta esta petición, verifica el JWT y extrae su identidad. |
| `routes` | `producto_routes.py` | Publica la ruta y conecta sus dependencias. |
| `controllers` | `producto_controller.py` | Llama al servicio y construye la respuesta. |
| `dtos` | `producto_dto.py` | Valida entrada y define la respuesta. |
| `service` | `producto_service.py` | Aplica las reglas de negocio, atribuye la sucursal y prepara la auditoría. |
| `repositories` | `producto_repository.py` | Ejecuta SQL explícito (`SELECT`, `JOIN`, `INSERT ... RETURNING`) con parámetros. |
| `exceptions` | `producto_exceptions.py`, `handlers.py` | Define errores de negocio y su traducción a HTTP. |
| `models` | Modelos de productos, categorías, inventario y movimientos | Define las entidades utilizadas. |

Las importaciones apuntan directamente a esos cuatro modelos dentro de `models`, sin archivos de compatibilidad duplicados. Las tablas, columnas y relaciones se mantienen: esta historia no requiere una migración de esquema.

El POST genérico anterior de productos deja de publicarse para que exista una sola ruta de registro. Los routers están unificados en `routes` y los servicios en `service`. La separación interna en controller y repository de los otros casos de uso se abordará en sus respectivas historias.

## SQL explícito en repositories

Las consultas de esta historia se escriben mediante `text()` y se ejecutan con
`Session.execute()`. Por ejemplo:

```python
consulta = text("SELECT id, sku FROM productos WHERE sku = :sku")
fila = self.db.execute(consulta, {"sku": sku}).mappings().first()
```

Los valores se pasan por separado; no se interpolan dentro del SQL. El resultado
se convierte en un diccionario que consume el servicio. Los `INSERT` incluyen
`RETURNING` para recuperar el ID y los valores persistidos sin una consulta extra.
Los tipos de parámetros y resultados mantienen los valores decimales y las fechas.

Los modelos siguen definiendo las tablas. En este repositorio no se utiliza
`select(Model)`, `db.add()` ni `flush()` para construir o ejecutar las operaciones.
SQLAlchemy conserva la conexión, los parámetros y la transacción existente.
PostgreSQL utiliza `FOR UPDATE` y `FOR SHARE` para los bloqueos; SQLite se usa
únicamente para las pruebas rápidas y no implementa esas cláusulas.

## Errores

| Estado | Caso |
|---|---|
| 401 | Token ausente/inválido/expirado o usuario inexistente/inactivo. |
| 403 | Rol diferente de operador o sucursal no disponible. |
| 404 | Categoría inexistente. |
| 409 | SKU existente, incluso ante dos registros concurrentes. |
| 422 | Campos vacíos, cantidad no positiva, mínimo/costo negativo, precisión excesiva o campos adicionales. |

## Comprobaciones

`tests/test_registro_producto.py` cubre registro y trazabilidad persistidos, mínimos por sucursal, permisos, datos inválidos, protección del responsable y la sucursal, SKU duplicado, repetición de petición y rollback por fallo en auditoría. Incluye una prueba sobre PostgreSQL de dos sucursales registrando simultáneamente el mismo SKU.

```bash
pytest -q tests/test_registro_producto.py
```

Para incluir concurrencia, usar una base de prueba PostgreSQL mediante `TEST_DATABASE_URL`, como se describe en el README. La conexión de la aplicación no se modifica.
