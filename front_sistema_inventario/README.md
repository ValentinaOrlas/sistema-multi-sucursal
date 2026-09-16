# Nodo · Inventario multisucursal

Frontend React conectado a la API FastAPI. Esta entrega cubre RF-INV-01 a RF-INV-05.

## Arranque

Desde la raíz del proyecto: `docker compose up -d --build`.

- Aplicación: http://localhost:5173
- API: http://localhost:8000/docs

Para desarrollo sin contenedores, ejecutar `npm install` y `npm run dev` en esta carpeta.
`VITE_API_URL` define la dirección del backend (por defecto http://localhost:8000).
Se utilizan las credenciales de usuarios existentes; no hay datos simulados en la aplicación.
La sesión se conserva en sessionStorage y se elimina al cerrar sesión o recibir un 401.

## Funciones

- Inventario de la sucursal seleccionada y catálogo general de productos.
- Consulta de stock de otras sucursales, búsqueda por SKU/nombre/descripción y filtros.
- Registro de producto con descripción, categoría, unidad, cantidad inicial, costo y mínimo local.
- Edición de atributos compartidos y eliminación confirmada cuando el backend la permite.
- Entradas y salidas con motivo, cantidad, fecha y responsable; control de stock insuficiente.
- Configuración de stock mínimo local, alertas y detalle de producto.
- Historial paginado en pantalla y carga de todas las páginas de la API.
- Actualización automática cada 15 segundos mientras la pestaña es visible, al volver a ella y después de una operación.
- Interfaz adaptable a móvil, navegación con teclado y diálogos modales.

## Permisos conservados

| Operación | Permiso |
|---|---|
| Crear producto | Operador, exclusivamente en su sucursal |
| Editar/eliminar producto y crear categoría | Administrador general |
| Configurar mínimo | Gerente de su sucursal o administrador |
| Movimientos | Usuarios autorizados por el backend para esa sucursal |
| Consultar stock de la red | Todos los usuarios autenticados |
| Consultar historial | Propia sucursal; administrador en cualquier sucursal |

El backend es la autoridad de permisos y validaciones. No se borra el historial: un
producto con inventario, movimientos o documentos asociados no puede eliminarse.
La unidad base de productos existentes se conserva para no alterar el significado
histórico de las cantidades. Los movimientos manuales no crean órdenes de compra
ni comprobantes de venta; esos módulos tendrán sus propias pantallas.

Las sucursales y asignaciones de usuarios se configuran mediante la API administrativa.
Si no existen categorías, el administrador puede crearlas en Catálogo de productos.

## Organización

Los archivos están directamente en `src`, sin nuevas subcarpetas:
`App.jsx` (sesión), `Inventory.jsx` (inventario), `InventoryForm.jsx` (formularios),
`api.js` (HTTP y formatos), `Icons.jsx` (iconos) y los estilos existentes.

## Verificación

`npm run build` y `npm run lint`.

Pruebas manuales en navegador realizadas con base y contenedores temporales:
registro, búsqueda por SKU, bloqueo por stock insuficiente, retiro válido e historial,
consulta restringida de otra sucursal, edición, mínimo local y vista móvil.
El backend incluye una regresión que verifica la persistencia de la descripción.

## Módulo de Compras

Disponible en el menú **Compras**, conectado a las rutas existentes del backend.

- Crear órdenes de hasta 100 productos distintos, en su unidad base.
- Capturar precio unitario, descuento por línea y plazo de pago en días.
- Filtrar el histórico por sucursal, proveedor, producto y estado.
- Consultar el detalle y confirmar la recepción completa de mercancía.
- Cancelar órdenes pendientes como administrador o gerente autorizado.
- Crear y editar proveedores como administrador; consulta para los demás roles.
- Actualizar automáticamente las listas cada 15 segundos y tras las operaciones.

La recepción y el cálculo de costo promedio se ejecutan exclusivamente en el
backend, en una transacción con los movimientos auditables. Los importes del
formulario son estimaciones de presentación, sin impuestos adicionales.
No se modifican las tablas ni los permisos existentes. Las órdenes recibidas o
canceladas no ofrecen acciones de recepción. La recepción parcial de compras
no está soportada por el backend actual.

Prueba de navegador en base temporal: proveedor nuevo, orden de 10 unidades a
100 con descuento del 10 % y plazo de 30 días, recepción confirmada y consulta de
stock. Comprobación en PostgreSQL: stock 10, costo promedio 90, movimiento con
fecha, usuario receptor, motivo y referencia de compra. Compilación y lint sin errores.
