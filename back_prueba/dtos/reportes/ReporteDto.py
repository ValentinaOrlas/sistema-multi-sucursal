from enum import Enum

class TipoReporte(str, Enum):
    VENTAS = "ventas"
    MOVIMIENTOS = "movimientos"
    TRANSFERENCIAS = "transferencias"

class FormatoReporte(str, Enum):
    EXCEL = "excel"
    PDF = "pdf"