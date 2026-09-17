from repositories.transferencias.TransferenciaRepositorio import TransferenciasRepositorio
from conection.conectionDb import con_cursor

class TransferenciasService:

    @staticmethod
    @con_cursor
    def solicitar_transferencia(cur, datos: dict) -> tuple:
        try:
            origen_id = datos['sucursal_origen_id']
            destino_id = datos['sucursal_destino_id']
            
            if origen_id == destino_id:
                return {"error": "La sucursal de origen y destino no pueden ser la misma"}, 400

            transferencia_id = TransferenciasRepositorio.crear_transferencia(
                cur, origen_id, destino_id, datos['usuario_solicitante_id'], datos['prioridad']
            )

            for item in datos['detalles']:
                TransferenciasRepositorio.crear_detalle_transferencia(
                    cur, transferencia_id, item['producto_id'], item['cantidad_solicitada']
                )

            return {"mensaje": "Solicitud de transferencia creada exitosamente", "transferencia_id": transferencia_id}, 201
        except Exception as e:
            return {"error": str(e)}, 400

    @staticmethod
    @con_cursor
    def preparar_y_enviar_transferencia(cur, transferencia_id: int, datos: dict) -> tuple:
        try:
            transf = TransferenciasRepositorio.obtener_transferencia_por_id(cur, transferencia_id)
            if not transf:
                return {"error": "Transferencia no encontrada"}, 404
            
            if transf['estado'] not in ['SOLICITADA', 'EN_PREPARACION']:
                return {"error": f"No se puede despachar una transferencia en estado {transf['estado']}"}, 400

            sucursal_origen_id = transf['sucursal_origen_id']

            # Cambiar a preparando primero
            TransferenciasRepositorio.actualizar_a_en_preparacion(cur, transferencia_id)

            # Validar stock y descontar en origen (al pasar a EN_TRANSITO)
            for envio_item in datos['detalles']:
                producto_id = envio_item['producto_id']
                cantidad_enviada = envio_item['cantidad_enviada']

                inv_origen = TransferenciasRepositorio.obtener_inventario(cur, sucursal_origen_id, producto_id)
                if not inv_origen or inv_origen['stock_actual'] < cantidad_enviada:
                    return {"error": f"Stock insuficiente en la sucursal de origen para el producto ID {producto_id}"}, 400

                # Actualizar detalle de lo que realmente se envía
                TransferenciasRepositorio.actualizar_detalle_envio(cur, transferencia_id, producto_id, cantidad_enviada)

                # Descontar stock en origen y registrar movimiento de RETIRO
                nuevo_stock_origen = inv_origen['stock_actual'] - cantidad_enviada
                TransferenciasRepositorio.actualizar_stock_inventario(cur, sucursal_origen_id, producto_id, nuevo_stock_origen)
                TransferenciasRepositorio.registrar_movimiento(cur, sucursal_origen_id, producto_id, cantidad_enviada, 'RETIRO', nuevo_stock_origen)

            # Registrar el envío con transportista y fecha estimada
            TransferenciasRepositorio.registrar_envio(
                cur, transferencia_id, datos.get('transportista'), datos.get('fecha_estimada_llegada')
            )

            return {"mensaje": "Transferencia despachada correctamente (En tránsito y stock descontado en origen)"}, 200
        except Exception as e:
            return {"error": str(e)}, 400

    @staticmethod
    @con_cursor
    def confirmar_recepcion(cur, transferencia_id: int, datos: dict) -> tuple:
        try:
            transf = TransferenciasRepositorio.obtener_transferencia_por_id(cur, transferencia_id)
            if not transf:
                return {"error": "Transferencia no encontrada"}, 404
            
            if transf['estado'] != 'EN_TRANSITO':
                return {"error": "Solo se pueden recibir transferencias que se encuentren en estado EN_TRANSITO"}, 400

            sucursal_destino_id = transf['sucursal_destino_id']
            hubo_faltantes = False

            for item_recibido in datos['detalles']:
                producto_id = item_recibido['producto_id']
                cantidad_recibida = item_recibido['cantidad_recibida']
                tratamiento = item_recibido.get('tratamiento_faltante')

                # Buscar la cantidad enviada originalmente en el detalle de la transferencia
                detalle_original = next((d for d in transf['detalles'] if d['producto_id'] == producto_id), None)
                if not detalle_original:
                    return {"error": f"El producto ID {producto_id} no pertenece a esta transferencia"}, 400

                cantidad_enviada = detalle_original['cantidad_enviada']
                if cantidad_recibida > cantidad_enviada:
                    return {"error": f"No puedes recibir más de lo que fue enviado para el producto ID {producto_id}"}, 400

                faltantes = cantidad_enviada - cantidad_recibida
                if faltantes > 0:
                    hubo_faltantes = True
                    if not tratamiento or tratamiento == "None":
                        return {"error": f"Existen faltantes para el producto ID {producto_id}. Debe definir un tratamiento obligatoriamente (REENVIO, AJUSTE o RECLAMACION)"}, 400

                # Actualizar detalle de recepción y faltantes
                TransferenciasRepositorio.actualizar_detalle_recepcion(
                    cur, transferencia_id, producto_id, cantidad_recibida, faltantes, tratamiento
                )

                # Actualizar inventario en la sucursal destino si la cantidad recibida es mayor a 0
                if cantidad_recibida > 0:
                    # Obtenemos el CPP del origen para pasarlo al destino coherentemente
                    inv_origen = TransferenciasRepositorio.obtener_inventario(cur, transf['sucursal_origen_id'], producto_id)
                    cpp = inv_origen['costo_promedio_ponderado'] if inv_origen else 0.00

                    inv_destino = TransferenciasRepositorio.obtener_inventario(cur, sucursal_destino_id, producto_id)
                    if inv_destino:
                        nuevo_stock_destino = inv_destino['stock_actual'] + cantidad_recibida
                        TransferenciasRepositorio.actualizar_stock_inventario(cur, sucursal_destino_id, producto_id, nuevo_stock_destino)
                        stock_res = nuevo_stock_destino
                    else:
                        stock_res = cantidad_recibida
                        TransferenciasRepositorio.insertar_inventario_destino(cur, sucursal_destino_id, producto_id, stock_res, cpp)

                    TransferenciasRepositorio.registrar_movimiento(cur, sucursal_destino_id, producto_id, cantidad_recibida, 'INGRESO', stock_res)

            # Definir estado final según existencia de faltantes
            estado_final = 'RECIBIDA_PARCIAL' if hubo_faltantes else 'RECIBIDA_COMPLETA'
            TransferenciasRepositorio.finalizar_transferencia(cur, transferencia_id, estado_final)

            mensaje = "Transferencia recibida parcialmente con alertas de faltantes registradas" if hubo_faltantes else "Transferencia recibida completa exitosamente"
            return {"mensaje": mensaje, "estado": estado_final}, 200

        except Exception as e:
            return {"error": str(e)}, 400

    @staticmethod
    @con_cursor
    def obtener_transferencia(cur, transferencia_id: int) -> tuple:
        transf = TransferenciasRepositorio.obtener_transferencia_por_id(cur, transferencia_id)
        if not transf:
            return {"error": "Transferencia no encontrada"}, 404
        return transf, 200