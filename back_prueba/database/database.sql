
CREATE TABLE sucursales (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(100) NOT NULL UNIQUE,
    ubicacion   VARCHAR(255) NOT NULL,
    activa      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE roles (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(50) NOT NULL UNIQUE,
    descripcion TEXT,
    CONSTRAINT chk_roles_nombre CHECK (nombre IN ('ADMIN_GENERAL', 'GERENTE_SUCURSAL', 'OPERADOR_INVENTARIO'))
);

CREATE TABLE usuarios (
    id            SERIAL PRIMARY KEY,
    nombre        VARCHAR(100) NOT NULL,
    email         VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    rol_id        INT NOT NULL REFERENCES roles(id),
    sucursal_id   INT NULL REFERENCES sucursales(id),
    activo        BOOLEAN NOT NULL DEFAULT TRUE
);


CREATE TABLE categorias (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(100) NOT NULL UNIQUE,
    descripcion TEXT
);


CREATE TABLE proveedores (
    id                            SERIAL PRIMARY KEY,
    nombre                        VARCHAR(150) NOT NULL,
    contacto                      VARCHAR(100),
    condiciones_comerciales       TEXT,
    tiempo_entrega_promedio_dias  INT NOT NULL CHECK (tiempo_entrega_promedio_dias >= 0)
);

CREATE TABLE productos (
    id                    SERIAL PRIMARY KEY,
    sku                   VARCHAR(100) NOT NULL UNIQUE,
    nombre                VARCHAR(150) NOT NULL,
    descripcion           TEXT,
    categoria_id          INT NOT NULL REFERENCES categorias(id),
    unidad_medida         VARCHAR(50) NOT NULL,
    stock_minimo_global   INT NOT NULL CHECK (stock_minimo_global >= 0)
);


CREATE TABLE inventario_sucursal (
    id                       SERIAL PRIMARY KEY,
    sucursal_id              INT NOT NULL REFERENCES sucursales(id),
    producto_id              INT NOT NULL REFERENCES productos(id),
    stock_actual             INT NOT NULL CHECK (stock_actual >= 0),
    stock_minimo_local       INT NOT NULL CHECK (stock_minimo_local >= 0),
    costo_promedio_ponderado NUMERIC(12,2) NOT NULL CHECK (costo_promedio_ponderado >= 0),
    UNIQUE (sucursal_id, producto_id)
);


CREATE TABLE ordenes_compra (
    id                  SERIAL PRIMARY KEY,
    proveedor_id        INT NOT NULL REFERENCES proveedores(id),
    sucursal_destino_id INT NOT NULL REFERENCES sucursales(id),
    usuario_id          INT NOT NULL REFERENCES usuarios(id),
    estado              VARCHAR(50) NOT NULL,
    fecha_creacion      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_recepcion     TIMESTAMP NULL,
    CONSTRAINT chk_ordenes_compra_estado CHECK (estado IN ('PENDIENTE', 'RECIBIDA', 'CANCELADA'))
);


CREATE TABLE detalle_orden_compra (
    id               SERIAL PRIMARY KEY,
    orden_compra_id  INT NOT NULL REFERENCES ordenes_compra(id) ON DELETE CASCADE,
    producto_id      INT NOT NULL REFERENCES productos(id),
    cantidad         INT NOT NULL CHECK (cantidad > 0),
    precio_unitario  NUMERIC(12,2) NOT NULL CHECK (precio_unitario >= 0),
    descuento        NUMERIC(5,2) NOT NULL DEFAULT 0.00
);

CREATE TABLE ventas (
    id           SERIAL PRIMARY KEY,
    sucursal_id  INT NOT NULL REFERENCES sucursales(id),
    usuario_id   INT NOT NULL REFERENCES usuarios(id),
    fecha_venta  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_venta  NUMERIC(12,2) NOT NULL CHECK (total_venta >= 0)
);


CREATE TABLE detalle_venta (
    id                  SERIAL PRIMARY KEY,
    venta_id            INT NOT NULL REFERENCES ventas(id) ON DELETE CASCADE,
    producto_id         INT NOT NULL REFERENCES productos(id),
    cantidad            INT NOT NULL CHECK (cantidad > 0),
    precio_unitario     NUMERIC(12,2) NOT NULL CHECK (precio_unitario >= 0),
    descuento_aplicado  NUMERIC(5,2) NOT NULL DEFAULT 0.00
);


CREATE TABLE transferencias (
    id                       SERIAL PRIMARY KEY,
    sucursal_origen_id       INT NOT NULL REFERENCES sucursales(id),
    sucursal_destino_id      INT NOT NULL REFERENCES sucursales(id),
    usuario_solicitante_id   INT NOT NULL REFERENCES usuarios(id),
    estado                   VARCHAR(50) NOT NULL,
    prioridad                VARCHAR(20) NOT NULL DEFAULT 'MEDIA',
    transportista            VARCHAR(150) NULL,
    fecha_estimada_llegada   TIMESTAMP NULL,
    fecha_real_llegada       TIMESTAMP NULL,
    created_at               TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_transferencias_estado CHECK (
        estado IN ('SOLICITADA', 'EN_PREPARACION', 'EN_TRANSITO', 'RECIBIDA_COMPLETA', 'RECIBIDA_PARCIAL', 'CANCELADA')
    ),
    CONSTRAINT chk_transferencias_prioridad CHECK (prioridad IN ('ALTA', 'MEDIA', 'BAJA'))
);


CREATE TABLE detalle_transferencia (
    id                     SERIAL PRIMARY KEY,
    transferencia_id       INT NOT NULL REFERENCES transferencias(id) ON DELETE CASCADE,
    producto_id            INT NOT NULL REFERENCES productos(id),
    cantidad               INT NOT NULL CHECK (cantidad > 0),
    cantidad_solicitada    INT NOT NULL CHECK (cantidad_solicitada > 0),
    cantidad_enviada       INT NOT NULL CHECK (cantidad_enviada >= 0),
    cantidad_recibida      INT NOT NULL CHECK (cantidad_recibida >= 0),
    faltantes              INT NOT NULL DEFAULT 0 CHECK (faltantes >= 0),
    tratamiento_faltante   VARCHAR(50) NULL,
    CONSTRAINT chk_detalle_transferencia_tratamiento CHECK (
        tratamiento_faltante IS NULL OR tratamiento_faltante IN ('REENVIO', 'AJUSTE', 'RECLAMACION')
    )
);


CREATE TABLE movimientos_inventario (
    id                SERIAL PRIMARY KEY,
    sucursal_id       INT NOT NULL REFERENCES sucursales(id),
    producto_id       INT NOT NULL REFERENCES productos(id),
    cantidad          INT NOT NULL CHECK (cantidad > 0),
    tipo_movimiento   VARCHAR(20) NOT NULL CHECK (tipo_movimiento IN ('INGRESO', 'RETIRO')),
    motivo            VARCHAR(100) NOT NULL,
    stock_resultante  INT NOT NULL CHECK (stock_resultante >= 0),
    fecha_movimiento  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_movimientos_motivo CHECK (
        motivo IN ('COMPRA', 'VENTA', 'TRANSFERENCIA', 'MERMA', 'DEVOLUCION', 'AJUSTE')
    )
);

CREATE TABLE producto_proveedor (
    id                    SERIAL PRIMARY KEY,
    proveedor_id          INT NOT NULL REFERENCES proveedores(id) ON DELETE CASCADE,
    producto_id           INT NOT NULL REFERENCES productos(id) ON DELETE CASCADE,
    precio_referencia     NUMERIC(12,2) NULL CHECK (precio_referencia >= 0),
    activo                BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (proveedor_id, producto_id)
);


multi_sucursal=# INSERT INTO sucursales (nombre, ubicacion, activa) VALUES
multi_sucursal-# ('Sucursal Central Bogotá', 'Calle 100 # 15-20, Bogotá D.C.', TRUE),
multi_sucursal-# ('Sucursal Norte Medellín', 'Carrera 43A # 1 Sur-150, Medellín', TRUE),
multi_sucursal-# ('Sucursal Cali Sur', 'Centro Comercial Unicentro, Local 124, Cali', TRUE);
INSERT 0 3
multi_sucursal=# INSERT INTO roles (nombre, descripcion) VALUES
multi_sucursal-# ('ADMIN_GENERAL', 'Administrador con acceso total a todas las sucursales y configuraciones del sistema.'),
multi_sucursal-# ('GERENTE_SUCURSAL', 'Gerente encargado de supervisar el inventario, compras y ventas de su respectiva sucursal.'),
multi_sucursal-# ('OPERADOR_INVENTARIO', 'Operador encargado de registrar entradas, salidas y movimientos físicos en el almacén.');
INSERT 0 3
multi_sucursal=# INSERT INTO usuarios (nombre, email, password_hash, rol_id, sucursal_id, activo) VALUES
multi_sucursal-# ('Carlos Administrador', 'admin@techstock.com', 'Admin123*', 1, NULL, TRUE),
multi_sucursal-# ('Ana Pérez', 'gerente.bogota@techstock.com', 'Gerente2026$', 2, 1, TRUE),
multi_sucursal-# ('Luis Gómez', 'operador.bogota@techstock.com', 'Operador123', 3, 1, TRUE),
multi_sucursal-# ('Sofia Torres', 'gerente.medellin@techstock.com', 'Medellin2026#', 2, 2, TRUE);
INSERT 0 4
multi_sucursal=# INSERT INTO categorias (nombre, descripcion) VALUES
multi_sucursal-# ('Laptops y Computadores', 'Equipos portátiles, computadores de escritorio y estaciones de trabajo.'),
multi_sucursal-# ('Smartphones y Telefonía', 'Teléfonos inteligentes, accesorios móviles y equipos de comunicación.'),
multi_sucursal-# ('Componentes de Hardware', 'Tarjetas gráficas, procesadores, memorias RAM, discos de estado sólido y placas base.'),
multi_sucursal-# ('Periféricos y Accesorios', 'Teclados mecánicos, ratones gamer, diademas, monitores y hubs USB.');
INSERT 0 4
multi_sucursal=# INSERT INTO proveedores (nombre, contacto, condiciones_comerciales, tiempo_entrega_promedio_dias) VALUES
multi_sucursal-# ('TechGlobal S.A.S.', 'ventas@techglobal.co', 'Pago a 30 días, envío gratuito en compras superiores a $5,000 USD.', 3),
multi_sucursal-# ('Imp_Tecnología Mayorista', 'contacto@imptec.com', 'Pago de contado con 5% de descuento, garantía directa de fábrica.', 5),
multi_sucursal-# ('Componentes del Sur', 'pedidos@compsur.net', 'Crédito a 15 días, pedidos mínimos de 10 unidades.', 2);
INSERT 0 3
multi_sucursal=# INSERT INTO productos (sku, nombre, descripcion, categoria_id, unidad_medida, stock_minimo_global) VALUES
multi_sucursal-# ('LAP-LEN-001', 'Laptop Lenovo Legion 5 Pro', 'Pantalla 16 pulgadas QHD, Ryzen 7, 16GB RAM, 512GB SSD, RTX 3060', 1, 'Unidad', 5),
multi_sucursal-# ('PH-SAM-020', 'Smartphone Samsung Galaxy S24 Ultra', 'Pantalla 6.8 pulgadas AMOLED, 256GB, 12GB RAM, Gris Titanio', 2, 'Unidad', 8),
multi_sucursal-# ('GPU-ASUS-308', 'Tarjeta Gráfica ASUS ROG Strix RTX 4070', '12GB GDDR6X, iluminación RGB, triple ventilador axial', 3, 'Unidad', 4),
multi_sucursal-# ('PER-LOG-502', 'Mouse Gamer Logitech G502 Hero', 'Sensor de alta precisión 25K, 11 botones programables, pesas ajustables', 4, 'Unidad', 10);
INSERT 0 4
multi_sucursal=# INSERT INTO inventario_sucursal (sucursal_id, producto_id, stock_actual, stock_minimo_local, costo_promedio_ponderado) VALUES
multi_sucursal-# (1, 1, 12, 3, 1200.00), -- Lenovo Legion en Bogotá
multi_sucursal-# (1, 2, 15, 4, 950.00),  -- Samsung S24 en Bogotá
multi_sucursal-# (1, 4, 25, 5, 45.50),   -- Mouse Logitech en Bogotá
multi_sucursal-# (2, 1, 2, 3, 1210.00),  -- Lenovo Legion en Medellín (Alerta: stock por debajo del mínimo)
multi_sucursal-# (2, 3, 6, 2, 780.00);   -- GPU ASUS en Medellín
INSERT 0 5
multi_sucursal=#  INSERT INTO ordenes_compra (proveedor_id, sucursal_destino_id, usuario_id, estado, fecha_recepcion) VALUES
multi_sucursal-# (1, 1, 2, 'RECIBIDA', '2026-09-10 14:30:00'),
multi_sucursal-# (2, 2, 4, 'PENDIENTE', NULL);
INSERT 0 2
multi_sucursal=# INSERT INTO detalle_orden_compra (orden_compra_id, producto_id, cantidad, precio_unitario, descuento) VALUES
multi_sucursal-# (1, 1, 10, 1150.00, 0.00),
multi_sucursal-# (1, 2, 15, 920.00, 50.00),
multi_sucursal-# (2, 3, 5, 750.00, 0.00);
INSERT 0 3
multi_sucursal=# INSERT INTO ventas (sucursal_id, usuario_id, fecha_venta, total_venta) VALUES
multi_sucursal-# (1, 3, '2026-09-15 10:15:00', 1395.50),
multi_sucursal-# (1, 3, '2026-09-16 16:45:00', 1045.00);
INSERT 0 2
multi_sucursal=# INSERT INTO detalle_venta (venta_id, producto_id, cantidad, precio_unitario, descuento_aplicado) VALUES
multi_sucursal-# (1, 1, 1, 1350.00, 0.00),
multi_sucursal-# (1, 4, 1, 50.00, 4.50),
multi_sucursal-# (2, 2, 1, 1045.00, 0.00);
INSERT 0 3
multi_sucursal=# INSERT INTO transferencias (sucursal_origen_id, sucursal_destino_id, usuario_solicitante_id, estado, prioridad, transportista, fecha_estimada_llegada) VALUES
multi_sucursal-# (1, 2, 4, 'EN_TRANSITO', 'ALTA', 'Deprisa Envíos', '2026-09-20 18:00:00');
INSERT 0 1
multi_sucursal=# INSERT INTO detalle_transferencia (transferencia_id, producto_id, cantidad, cantidad_solicitada, cantidad_enviada, cantidad_recibida, faltantes, tratamiento_faltante) VALUES
multi_sucursal-# (1, 1, 2, 2, 2, 0, 0, NULL);
INSERT 0 1
multi_sucursal=# INSERT INTO movimientos_inventario (sucursal_id, producto_id, cantidad, tipo_movimiento, motivo, stock_resultante) VALUES
multi_sucursal-# (1, 1, 10, 'INGRESO', 'COMPRA', 12),
multi_sucursal-# (1, 4, 1, 'RETIRO', 'VENTA', 25),
multi_sucursal-# (2, 1, 2, 'INGRESO', 'TRANSFERENCIA', 2);
INSERT 0 3
multi_sucursal=# INSERT INTO producto_proveedor (proveedor_id, producto_id, precio_referencia, activo) VALUES
multi_sucursal-# (1, 1, 1150.00, TRUE),
multi_sucursal-# (1, 2, 920.00, TRUE),
multi_sucursal-# (2, 3, 750.00, TRUE),
multi_sucursal-# (3, 4, 42.00, TRUE);
ERROR:  relation "producto_proveedor" does not exist
LINE 1: INSERT INTO producto_proveedor (proveedor_id, producto_id, p...
                    ^
multi_sucursal=# CREATE TABLE producto_proveedor (
multi_sucursal(#     id                    SERIAL PRIMARY KEY,
multi_sucursal(#     proveedor_id          INT NOT NULL REFERENCES proveedores(id) ON DELETE CASCADE,
multi_sucursal(#     producto_id           INT NOT NULL REFERENCES productos(id) ON DELETE CASCADE,
multi_sucursal(#     precio_referencia     NUMERIC(12,2) NULL CHECK (precio_referencia >= 0),
multi_sucursal(#     activo                BOOLEAN NOT NULL DEFAULT TRUE,
multi_sucursal(#     UNIQUE (proveedor_id, producto_id)
multi_sucursal(# );
CREATE TABLE
multi_sucursal=# INSERT INTO producto_proveedor (proveedor_id, producto_id, precio_referencia, activo) VALUES
(1, 1, 1150.00, TRUE),
(1, 2, 920.00, TRUE),
(2, 3, 750.00, TRUE),
(3, 4, 42.00, TRUE);
INSERT 0 4
multi_sucursal=# 



 id |        nombre        |             email              | password_hash | rol_id | sucursal_id | activo 
----+----------------------+--------------------------------+---------------+--------+-------------+--------
  1 | Carlos Administrador | admin@techstock.com            | Admin123*     |      1 |             | t
  2 | Ana Pérez            | gerente.bogota@techstock.com   | Gerente2026$  |      2 |           1 | t
  3 | Luis Gómez           | operador.bogota@techstock.com  | Operador123   |      3 |           1 | t
  4 | Sofia Torres         | gerente.medellin@techstock.com | Medellin2026# |      2 |           2 | t
(4 rows)

$ docker exec -it postgres_inventario psql -U admin_app -d multi_sucursal
