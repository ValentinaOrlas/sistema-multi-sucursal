from segurity.dependencias import admin_o_gerente, solo_admin
from fastapi import APIRouter, Response, Depends
from controllers.proveedor.proveedorControlador import ProveedoresControlador
from dtos.proveedor.ProveedorDto import (
    ProveedorCreateRequest,
    ProveedorUpdateRequest,
    AsociarProductoRequest
)

# 1. DEPENDENICA GLOBAL DEL ROUTER:
# Se cambia a `admin_o_gerente` porque el operador de inventario NO tiene acceso a proveedores.
router = APIRouter(
    prefix="/api/proveedores",
    tags=["Módulo de Gestión de Proveedores"],
    dependencies=[Depends(admin_o_gerente)] 
)

# --- GESTIÓN (Acceso: Exclusivo Administrador General) ---

@router.post("", status_code=201, dependencies=[Depends(solo_admin)])
def crear_proveedor(datos: ProveedorCreateRequest, response: Response):
    resultado, codigo_estado = ProveedoresControlador.crear_proveedor(datos.model_dump())
    response.status_code = codigo_estado
    return resultado

@router.put("/{proveedor_id}", status_code=200, dependencies=[Depends(solo_admin)])
def actualizar_proveedor(proveedor_id: int, datos: ProveedorUpdateRequest, response: Response):
    resultado, codigo_estado = ProveedoresControlador.actualizar_proveedor(proveedor_id, datos.model_dump())
    response.status_code = codigo_estado
    return resultado

@router.post("/{proveedor_id}/productos", status_code=200, dependencies=[Depends(solo_admin)])
def asociar_producto(proveedor_id: int, datos: AsociarProductoRequest, response: Response):
    resultado, codigo_estado = ProveedoresControlador.asociar_producto(proveedor_id, datos.model_dump())
    response.status_code = codigo_estado
    return resultado


# --- CONSULTAS (Acceso: Administrador General y Gerente de Sucursal) ---
# Al no tener un Depends() explícito, heredan "admin_o_gerente" del router.

@router.get("", status_code=200)
def listar_proveedores(response: Response):
    resultado, codigo_estado = ProveedoresControlador.listar_proveedores()
    response.status_code = codigo_estado
    return resultado

@router.get("/{proveedor_id}", status_code=200)
def obtener_proveedor(proveedor_id: int, response: Response):
    resultado, codigo_estado = ProveedoresControlador.obtener_proveedor(proveedor_id)
    response.status_code = codigo_estado
    return resultado

@router.get("/{proveedor_id}/evaluacion-entregas", status_code=200)
def evaluar_tiempos_entrega(proveedor_id: int, response: Response):
    resultado, codigo_estado = ProveedoresControlador.evaluar_tiempos(proveedor_id)
    response.status_code = codigo_estado
    return resultado