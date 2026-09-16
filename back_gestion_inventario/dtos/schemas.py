from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

Id = Annotated[int, Field(gt=0)]
Nombre = Annotated[str, Field(min_length=1, max_length=100)]
Cantidad = Annotated[Decimal, Field(gt=0, max_digits=14, decimal_places=3)]
NoNegativa = Annotated[Decimal, Field(ge=0, max_digits=14, decimal_places=3)]
Dinero = Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=2)]
Porcentaje = Annotated[Decimal, Field(ge=0, le=100, decimal_places=2)]


class Schema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True, extra="forbid", str_strip_whitespace=True
    )


class Login(Schema):
    email: EmailStr
    password: str


class RoleCreate(Schema):
    nombre: Literal["ADMIN_GENERAL", "GERENTE_SUCURSAL", "OPERADOR_INVENTARIO"]
    descripcion: str | None = None


class RoleUpdate(Schema):
    descripcion: str | None = None


class RoleResponse(RoleCreate):
    id: int


class SucursalCreate(Schema):
    nombre: Nombre
    ubicacion: Annotated[str, Field(min_length=1, max_length=255)]
    activa: bool = True


class SucursalUpdate(Schema):
    nombre: Nombre | None = None
    ubicacion: Annotated[str, Field(min_length=1, max_length=255)] | None = None
    activa: bool | None = None


class SucursalResponse(SucursalCreate):
    id: int
    created_at: datetime


class UsuarioCreate(Schema):
    nombre: Nombre
    email: EmailStr
    password: Annotated[str, Field(min_length=10, max_length=72)]
    rol_id: Id
    sucursal_id: Id | None = None


class UsuarioUpdate(Schema):
    nombre: Nombre | None = None
    email: EmailStr | None = None
    password: Annotated[str, Field(min_length=10, max_length=72)] | None = None
    rol_id: Id | None = None
    sucursal_id: Id | None = None
    activo: bool | None = None


class UsuarioResponse(Schema):
    id: int
    nombre: str
    email: EmailStr
    rol_id: int
    sucursal_id: int | None
    activo: bool
    rol: RoleResponse


class CategoriaCreate(Schema):
    nombre: Nombre
    descripcion: str | None = None


class CategoriaUpdate(Schema):
    nombre: Nombre | None = None
    descripcion: str | None = None


class CategoriaResponse(CategoriaCreate):
    id: int


class ProductoCreate(Schema):
    sku: Nombre
    nombre: Annotated[str, Field(min_length=1, max_length=150)]
    descripcion: str | None = None
    categoria_id: Id
    unidad_medida: Annotated[str, Field(min_length=1, max_length=50)]
    stock_minimo_global: NoNegativa = Decimal(0)


class ProductoUpdate(Schema):
    sku: Nombre | None = None
    nombre: Annotated[str, Field(min_length=1, max_length=150)] | None = None
    descripcion: str | None = None
    categoria_id: Id | None = None
    stock_minimo_global: NoNegativa | None = None


class ProductoResponse(ProductoCreate):
    id: int


class ProveedorCreate(Schema):
    nombre: Annotated[str, Field(min_length=1, max_length=150)]
    contacto: Nombre | None = None
    condiciones_comerciales: str | None = None
    tiempo_entrega_promedio_dias: Annotated[int, Field(ge=0)] = 0


class ProveedorUpdate(Schema):
    nombre: Annotated[str, Field(min_length=1, max_length=150)] | None = None
    contacto: Nombre | None = None
    condiciones_comerciales: str | None = None
    tiempo_entrega_promedio_dias: Annotated[int, Field(ge=0)] | None = None


class ProveedorResponse(ProveedorCreate):
    id: int


class UnidadCreate(Schema):
    nombre: Annotated[str, Field(min_length=1, max_length=50)]
    factor: Annotated[Decimal, Field(gt=0, max_digits=14, decimal_places=6)]


class UnidadResponse(UnidadCreate):
    id: int
    producto_id: int


class ListaCreate(Schema):
    nombre: Nombre


class ListaResponse(ListaCreate):
    id: int


class PrecioCreate(Schema):
    producto_id: Id
    precio: Dinero


class PrecioResponse(PrecioCreate):
    id: int
    lista_id: int


class InventarioSucursalCreate(Schema):
    sucursal_id: Id
    producto_id: Id
    stock_minimo_local: NoNegativa = Decimal(0)


class InventarioSucursalUpdate(Schema):
    stock_minimo_local: NoNegativa


class InventarioSucursalResponse(InventarioSucursalCreate):
    id: int
    stock_actual: Decimal
    costo_promedio_ponderado: Decimal


class MovimientoCreate(Schema):
    sucursal_id: Id
    producto_id: Id
    cantidad: Cantidad
    unidad_id: Id | None = None
    tipo_movimiento: Literal["INGRESO", "RETIRO"]
    motivo: Nombre
    costo_unitario: Dinero | None = None

    @model_validator(mode="after")
    def costo_ingreso(self):
        if self.tipo_movimiento == "INGRESO" and self.costo_unitario is None:
            raise ValueError("Un ingreso requiere costo_unitario por unidad indicada")
        return self


class MovimientoResponse(Schema):
    id: int
    sucursal_id: int
    producto_id: int
    usuario_id: int | None
    cantidad: Decimal
    tipo_movimiento: str
    motivo: str
    stock_resultante: Decimal
    costo_unitario: Decimal
    fecha_movimiento: datetime
    venta_id: int | None
    orden_compra_id: int | None
    transferencia_id: int | None


class DetalleVentaCreate(Schema):
    producto_id: Id
    cantidad: Cantidad
    unidad_id: Id | None = None
    precio_unitario: Dinero | None = None
    descuento_aplicado: Porcentaje = Decimal(0)


class VentaCreate(Schema):
    sucursal_id: Id
    lista_precio_id: Id | None = None
    detalles: Annotated[list[DetalleVentaCreate], Field(min_length=1, max_length=100)]


class DetalleVentaResponse(Schema):
    id: int
    producto_id: int
    cantidad: Decimal
    precio_unitario: Decimal
    descuento_aplicado: Decimal


class VentaResponse(Schema):
    id: int
    sucursal_id: int
    usuario_id: int
    fecha_venta: datetime
    total_venta: Decimal
    detalles: list[DetalleVentaResponse]


class DetalleOrdenCompraCreate(Schema):
    producto_id: Id
    cantidad: Cantidad
    unidad_id: Id | None = None
    precio_unitario: Dinero
    descuento: Porcentaje = Decimal(0)


class OrdenCompraCreate(Schema):
    proveedor_id: Id
    sucursal_destino_id: Id
    plazo_pago_dias: Annotated[int, Field(ge=0)] = 0
    detalles: Annotated[
        list[DetalleOrdenCompraCreate], Field(min_length=1, max_length=100)
    ]


class DetalleOrdenCompraResponse(Schema):
    id: int
    producto_id: int
    cantidad: Decimal
    precio_unitario: Decimal
    descuento: Decimal


class OrdenCompraResponse(Schema):
    id: int
    proveedor_id: int
    sucursal_destino_id: int
    usuario_id: int
    plazo_pago_dias: int
    estado: str
    fecha_creacion: datetime
    fecha_recepcion: datetime | None
    detalles: list[DetalleOrdenCompraResponse]


class TransferenciaDetalleCreate(Schema):
    producto_id: Id
    cantidad: Cantidad
    unidad_id: Id | None = None


class TransferenciaCreate(Schema):
    sucursal_origen_id: Id
    sucursal_destino_id: Id
    prioridad: Literal["BAJA", "MEDIA", "ALTA"] = "MEDIA"
    detalles: Annotated[
        list[TransferenciaDetalleCreate], Field(min_length=1, max_length=100)
    ]

    @model_validator(mode="after")
    def diferentes(self):
        if self.sucursal_origen_id == self.sucursal_destino_id:
            raise ValueError("Origen y destino deben ser diferentes")
        return self


class CantidadTransferencia(Schema):
    detalle_id: Id
    cantidad: NoNegativa


class PrepararTransferencia(Schema):
    detalles: Annotated[
        list[CantidadTransferencia], Field(min_length=1, max_length=100)
    ]


class DespacharTransferencia(Schema):
    transportista: Annotated[str, Field(min_length=1, max_length=150)]
    fecha_estimada_llegada: datetime
    costo_envio: Dinero = Decimal(0)
    ruta: Annotated[str, Field(min_length=1, max_length=150)]


class RecibirTransferencia(PrepararTransferencia):
    tratamiento_faltante: Literal["REENVIO", "AJUSTE", "RECLAMACION"] | None = None


class DetalleTransferenciaResponse(Schema):
    id: int
    producto_id: int
    cantidad_solicitada: Decimal
    cantidad_enviada: Decimal
    cantidad_recibida: Decimal
    faltantes: Decimal
    tratamiento_faltante: str | None
    costo_unitario: Decimal


class TransferenciaResponse(Schema):
    id: int
    sucursal_origen_id: int
    sucursal_destino_id: int
    usuario_solicitante_id: int
    prioridad: str
    estado: str
    transportista: str | None
    ruta: str | None
    costo_envio: Decimal
    fecha_despacho: datetime | None
    fecha_estimada_llegada: datetime | None
    fecha_real_llegada: datetime | None
    created_at: datetime
    detalles: list[DetalleTransferenciaResponse]
