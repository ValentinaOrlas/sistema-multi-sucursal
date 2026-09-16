from datetime import datetime, timezone
from decimal import Decimal

from core.dependencies import branch_access
from fastapi import HTTPException
from models import (
    DetalleOrdenCompraModel,
    DetalleTransferenciaModel,
    DetalleVentaModel,
    ListaPrecioModel,
    OrdenCompraModel,
    PrecioProductoModel,
    ProveedorModel,
    TransferenciaModel,
    VentaModel,
)
from repositories import inventario_repository as repo

from service.inventario_service import (
    cost,
    lock_branches,
    money,
    move,
    normalize,
    require,
    stock,
)


def now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def unique_products(details):
    if len({d.producto_id for d in details}) != len(details):
        raise HTTPException(422, "No repitas productos en los detalles")


def locked(db, model, identity):
    row = repo.get(db, model, identity, lock=True)
    if row is None:
        raise HTTPException(404, "Documento no encontrado")
    return row


def state(row, expected):
    if row.estado != expected:
        raise HTTPException(
            409, f"La operación requiere estado {expected}; estado actual: {row.estado}"
        )


def create_sale(db, user, data):
    branch_access(user, data.sucursal_id)
    lock_branches(db, data.sucursal_id)
    unique_products(data.detalles)
    if data.lista_precio_id is not None:
        require(db, ListaPrecioModel, data.lista_precio_id)
    sale = VentaModel(
        sucursal_id=data.sucursal_id, usuario_id=user.id, total_venta=Decimal(0)
    )
    repo.save(db, sale)
    for item in data.detalles:
        qty, factor = normalize(db, item.producto_id, item.cantidad, item.unidad_id)
        if data.lista_precio_id is not None:
            if item.precio_unitario is not None:
                raise HTTPException(422, "Usa precio manual o lista, no ambos")
            price = repo.find(
                db,
                PrecioProductoModel,
                lista_id=data.lista_precio_id,
                producto_id=item.producto_id,
            )
            if price is None:
                raise HTTPException(422, "Producto sin precio en la lista")
            unit_price = price.precio
        elif item.precio_unitario is not None:
            unit_price = cost(item.precio_unitario / factor)
        else:
            raise HTTPException(
                422, "Cada producto requiere precio o una lista de precios"
            )
        sale.detalles.append(
            DetalleVentaModel(
                producto_id=item.producto_id,
                cantidad=qty,
                precio_unitario=unit_price,
                descuento_aplicado=item.descuento_aplicado,
            )
        )
        sale.total_venta += money(
            qty * unit_price * (1 - item.descuento_aplicado / 100)
        )
        move(
            db,
            user,
            sale.sucursal_id,
            item.producto_id,
            qty,
            "RETIRO",
            "Venta",
            venta_id=sale.id,
        )
    repo.save(db, sale)
    return sale


def create_purchase(db, user, data):
    branch_access(user, data.sucursal_destino_id)
    lock_branches(db, data.sucursal_destino_id)
    require(db, ProveedorModel, data.proveedor_id)
    unique_products(data.detalles)
    order = OrdenCompraModel(
        proveedor_id=data.proveedor_id,
        sucursal_destino_id=data.sucursal_destino_id,
        usuario_id=user.id,
        plazo_pago_dias=data.plazo_pago_dias,
    )
    for item in data.detalles:
        qty, factor = normalize(db, item.producto_id, item.cantidad, item.unidad_id)
        order.detalles.append(
            DetalleOrdenCompraModel(
                producto_id=item.producto_id,
                cantidad=qty,
                precio_unitario=cost(item.precio_unitario / factor),
                descuento=item.descuento,
            )
        )
    repo.save(db, order)
    return order


def receive_purchase(db, user, identity):
    order = locked(db, OrdenCompraModel, identity)
    branch_access(user, order.sucursal_destino_id)
    state(order, "PENDIENTE")
    lock_branches(db, order.sucursal_destino_id)
    for item in order.detalles:
        move(
            db,
            user,
            order.sucursal_destino_id,
            item.producto_id,
            item.cantidad,
            "INGRESO",
            "Recepción de compra",
            item.precio_unitario * (1 - item.descuento / 100),
            orden_compra_id=order.id,
        )
    order.estado, order.fecha_recepcion = "RECIBIDA", now()
    repo.save(db, order)
    return order


def create_transfer(db, user, data):
    branch_access(user, data.sucursal_destino_id)
    lock_branches(db, data.sucursal_origen_id, data.sucursal_destino_id)
    unique_products(data.detalles)
    transfer = TransferenciaModel(
        sucursal_origen_id=data.sucursal_origen_id,
        sucursal_destino_id=data.sucursal_destino_id,
        prioridad=data.prioridad,
        usuario_solicitante_id=user.id,
    )
    for item in data.detalles:
        qty, _ = normalize(db, item.producto_id, item.cantidad, item.unidad_id)
        transfer.detalles.append(
            DetalleTransferenciaModel(
                producto_id=item.producto_id, cantidad=qty, cantidad_solicitada=qty
            )
        )
    repo.save(db, transfer)
    return transfer


def quantities(row, data):
    values = {d.detalle_id: d.cantidad for d in data.detalles}
    if len(values) != len(data.detalles) or set(values) != {d.id for d in row.detalles}:
        raise HTTPException(422, "Incluye cada detalle exactamente una vez")
    return values


def prepare_transfer(db, user, identity, data):
    row = locked(db, TransferenciaModel, identity)
    branch_access(user, row.sucursal_origen_id, manager=True)
    state(row, "SOLICITADA")
    lock_branches(db, row.sucursal_origen_id, row.sucursal_destino_id)
    values = quantities(row, data)
    if not any(values.values()):
        raise HTTPException(
            422, "Debe prepararse al menos una unidad de algún producto"
        )
    for item in row.detalles:
        qty = values[item.id]
        if qty > item.cantidad_solicitada:
            raise HTTPException(422, "No puedes enviar más de lo solicitado")
        if stock(db, row.sucursal_origen_id, item.producto_id).stock_actual < qty:
            raise HTTPException(409, "Stock insuficiente para preparar")
        item.cantidad_enviada = qty
    row.estado = "PREPARADA"
    repo.save(db, row)
    return row


def dispatch_transfer(db, user, identity, data):
    row = locked(db, TransferenciaModel, identity)
    branch_access(user, row.sucursal_origen_id)
    state(row, "PREPARADA")
    eta = data.fecha_estimada_llegada
    if eta.tzinfo is None:
        raise HTTPException(
            422, "La fecha estimada requiere zona horaria, por ejemplo -05:00"
        )
    eta = eta.astimezone(timezone.utc).replace(tzinfo=None)
    if eta <= now():
        raise HTTPException(422, "La llegada estimada debe ser futura")
    lock_branches(db, row.sucursal_origen_id, row.sucursal_destino_id)
    for item in row.detalles:
        if item.cantidad_enviada:
            movement = move(
                db,
                user,
                row.sucursal_origen_id,
                item.producto_id,
                item.cantidad_enviada,
                "RETIRO",
                "Despacho de transferencia",
                transferencia_id=row.id,
            )
            item.costo_unitario = movement.costo_unitario
    row.estado = "EN_TRANSITO"
    row.fecha_despacho, row.fecha_estimada_llegada = now(), eta
    row.transportista, row.costo_envio, row.ruta = (
        data.transportista,
        data.costo_envio,
        data.ruta,
    )
    repo.save(db, row)
    return row


def receive_transfer(db, user, identity, data):
    row = locked(db, TransferenciaModel, identity)
    branch_access(user, row.sucursal_destino_id)
    state(row, "EN_TRANSITO")
    lock_branches(db, row.sucursal_origen_id, row.sucursal_destino_id)
    values = quantities(row, data)
    missing = False
    for item in row.detalles:
        qty = values[item.id]
        if qty > item.cantidad_enviada:
            raise HTTPException(422, "Cantidad recibida mayor que la enviada")
        item.cantidad_recibida = qty
        item.faltantes = item.cantidad_enviada - qty
        if item.faltantes:
            missing = True
            if data.tratamiento_faltante is None:
                raise HTTPException(422, "Indica tratamiento de faltantes")
            item.tratamiento_faltante = data.tratamiento_faltante
        if qty:
            move(
                db,
                user,
                row.sucursal_destino_id,
                item.producto_id,
                qty,
                "INGRESO",
                "Recepción de transferencia",
                item.costo_unitario,
                transferencia_id=row.id,
            )
    row.estado = "CON_FALTANTES" if missing else "RECIBIDA"
    row.fecha_real_llegada = now()
    repo.save(db, row)
    return row
