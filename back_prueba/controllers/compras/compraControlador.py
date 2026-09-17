from service.compras.CompraService import ComprasService as S

class ComprasControlador:
    crear = staticmethod(S.crear)
    listar = staticmethod(S.listar)
    obtener = staticmethod(S.obtener)
    recibir = staticmethod(S.recibir)
    cancelar = staticmethod(S.cancelar)
