# models/__init__.py

from conection.conectionDb import Base

# Importación de todos los modelos del sistema
from .sucursalesModel import SucursalesModel
from .rolesModel import RoleModel
from .categoriasModel import CategoriaModel
from .usuariosModel import UsuarioModel
from .proveedoresModel import ProveedorModel
from .productosModel import ProductoModel
from .inventarioSucursalModel import InventarioSucursalModel
from .ordenesCompraModel import OrdenCompraModel
from .detalleOrdenCompraModel import DetalleOrdenCompraModel
from .ventasModel import VentaModel
from .detalleVentaModel import DetalleVentaModel
from .transferenciasModel import TransferenciaModel
from .detalleTransferenciaModel import DetalleTransferenciaModel
from .movimientosInventarioModel import MovimientosInventarioModel

# Exportación centralizada
__all__ = [
    "Base",
    "SucursalesModel",
    "RoleModel",
    "CategoriaModel",
    "UsuarioModel",
    "ProveedorModel",
    "ProductoModel",
    "InventarioSucursalModel",
    "OrdenCompraModel",
    "DetalleOrdenCompraModel",
    "VentaModel",
    "DetalleVentaModel",
    "TransferenciaModel",
    "DetalleTransferenciaModel",
    "MovimientosInventarioModel",
]