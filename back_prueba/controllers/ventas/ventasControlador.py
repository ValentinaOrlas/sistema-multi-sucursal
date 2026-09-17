from service.ventas.VentaService import VentasService as S

class VentasControlador:
    registrar_venta = staticmethod(S.registrar_venta)
    obtener_comprobante = staticmethod(S.obtener_comprobante)
    listar = staticmethod(S.listar)
    listas = staticmethod(S.listas)
    precios = staticmethod(S.precios)
