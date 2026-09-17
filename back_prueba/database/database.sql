
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