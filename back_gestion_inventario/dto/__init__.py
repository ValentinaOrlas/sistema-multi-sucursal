# dto/__init__.py

from .rolesDto import RoleCreate, RoleUpdate, RoleResponse
from .sucursalesDto import SucursalCreate, SucursalUpdate, SucursalResponse
from .usuariosDto import UsuarioCreate, UsuarioUpdate, UsuarioResponse
from .categoriasDto import CategoriaCreate, CategoriaUpdate, CategoriaResponse
from .productosDto import ProductoCreate, ProductoUpdate, ProductoResponse
from .proveedoresDto import ProveedorCreate, ProveedorUpdate, ProveedorResponse
from .inventarioSucursalDto import InventarioSucursalCreate, InventarioSucursalUpdate, InventarioSucursalResponse
from .ventasDto import VentaCreate, VentaResponse, DetalleVentaCreate, DetalleVentaResponse
from .ordenesCompraDto import OrdenCompraCreate, OrdenCompraResponse, DetalleOrdenCompraCreate, DetalleOrdenCompraResponse

__all__ = [
    "RoleCreate", "RoleUpdate", "RoleResponse",
    "SucursalCreate", "SucursalUpdate", "SucursalResponse",
    "UsuarioCreate", "UsuarioUpdate", "UsuarioResponse",
    "CategoriaCreate", "CategoriaUpdate", "CategoriaResponse",
    "ProductoCreate", "ProductoUpdate", "ProductoResponse",
    "ProveedorCreate", "ProveedorUpdate", "ProveedorResponse",
    "InventarioSucursalCreate", "InventarioSucursalUpdate", "InventarioSucursalResponse",
    "VentaCreate", "VentaResponse", "DetalleVentaCreate", "DetalleVentaResponse",
    "OrdenCompraCreate", "OrdenCompraResponse", "DetalleOrdenCompraCreate", "DetalleOrdenCompraResponse"
]