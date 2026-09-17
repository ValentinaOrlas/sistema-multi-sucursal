import React, { useState, useEffect } from 'react';

const API_URL = 'http://localhost:8000/api/proveedores';

export default function ProveedoresManager() {
  const [proveedores, setProveedores] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [proveedorSeleccionado, setProveedorSeleccionado] = useState(null);
  const [evaluacion, setEvaluacion] = useState(null);

  // Simulación de obtención de token (ajústalo a tu lógica de autenticación)
  const token = localStorage.getItem('token'); 
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  };

  useEffect(() => { 
    cargarProveedores();
  }, []);

  const cargarProveedores = async () => {
    try {
      setLoading(true);
      const res = await fetch(API_URL, { headers });
      if (!res.ok) throw new Error('Error al cargar proveedores. Verifica tus permisos.');
      const data = await res.json();
      setProveedores(data.proveedores || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const verDetalle = async (id) => {
    try {
      // Cargar detalle del proveedor
      const resDetalle = await fetch(`${API_URL}/${id}`, { headers });
      if (!resDetalle.ok) throw new Error('Error al cargar detalle');
      const dataDetalle = await resDetalle.json();
      setProveedorSeleccionado(dataDetalle);

      // Cargar evaluación de tiempos
      const resEval = await fetch(`${API_URL}/${id}/evaluacion-entregas`, { headers });
      if (resEval.ok) {
        const dataEval = await resEval.json();
        setEvaluacion(dataEval);
      }
    } catch (err) {
      alert(err.message);
    }
  };

  if (loading) return <div className="p-4 text-gray-600">Cargando proveedores...</div>;
  if (error) return <div className="p-4 text-red-500">Error: {error}</div>;

  return (
    <div className="p-6 max-w-7xl mx-auto flex flex-col md:flex-row gap-6">
      
      {/* SECCIÓN IZQUIERDA: Lista de Proveedores */}
      <div className="w-full md:w-1/2 bg-white rounded-lg shadow p-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-gray-800">Directorio de Proveedores</h2>
          <button className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 text-sm">
            + Nuevo Proveedor
          </button>
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm whitespace-nowrap">
            <thead className="uppercase tracking-wider border-b-2 border-gray-200 bg-gray-50 text-gray-600">
              <tr>
                <th className="px-4 py-3">Nombre</th>
                <th className="px-4 py-3">Contacto</th>
                <th className="px-4 py-3 text-center">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {proveedores.map((prov) => (
                <tr key={prov.id} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{prov.nombre}</td>
                  <td className="px-4 py-3 text-gray-600">{prov.contacto || 'N/A'}</td>
                  <td className="px-4 py-3 text-center">
                    <button 
                      onClick={() => verDetalle(prov.id)}
                      className="text-blue-600 hover:text-blue-800 font-semibold"
                    >
                      Ver Detalle
                    </button>
                  </td>
                </tr>
              ))}
              {proveedores.length === 0 && (
                <tr>
                  <td colSpan="3" className="px-4 py-4 text-center text-gray-500">
                    No hay proveedores registrados.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* SECCIÓN DERECHA: Detalle y Evaluación */}
      <div className="w-full md:w-1/2">
        {proveedorSeleccionado ? (
          <div className="bg-white rounded-lg shadow p-6 flex flex-col gap-6">
            
            {/* Información Básica */}
            <div>
              <h2 className="text-2xl font-bold text-gray-800 mb-2">{proveedorSeleccionado.nombre}</h2>
              <div className="text-sm text-gray-600 space-y-1">
                <p><strong>Contacto:</strong> {proveedorSeleccionado.contacto}</p>
                <p><strong>Condiciones:</strong> {proveedorSeleccionado.condiciones_comerciales}</p>
                <p><strong>Tiempo de entrega pactado:</strong> {proveedorSeleccionado.tiempo_entrega_promedio_dias} días</p>
              </div>
            </div>

            {/* Evaluación de Desempeño */}
            {evaluacion && (
              <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                <h3 className="text-lg font-bold text-gray-800 mb-3">Evaluación de Entregas</h3>
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div className="bg-white p-3 rounded shadow-sm border">
                    <p className="text-xs text-gray-500 uppercase">Promedio Real</p>
                    <p className="text-xl font-bold text-blue-600">{evaluacion.tiempo_promedio_real_calculado} días</p>
                  </div>
                  <div className="bg-white p-3 rounded shadow-sm border">
                    <p className="text-xs text-gray-500 uppercase">Órdenes Evaluadas</p>
                    <p className="text-xl font-bold text-gray-800">{evaluacion.total_ordenes_evaluadas}</p>
                  </div>
                </div>

                {evaluacion.detalle_ordenes?.length > 0 ? (
                  <div className="max-h-48 overflow-y-auto">
                    <table className="w-full text-sm text-left">
                      <thead className="bg-gray-200 text-gray-600 text-xs uppercase">
                        <tr>
                          <th className="px-2 py-1">Orden</th>
                          <th className="px-2 py-1 text-center">Días</th>
                          <th className="px-2 py-1">Estado</th>
                        </tr>
                      </thead>
                      <tbody>
                        {evaluacion.detalle_ordenes.map((orden) => (
                          <tr key={orden.orden_compra_id} className="border-b">
                            <td className="px-2 py-2">#{orden.orden_compra_id}</td>
                            <td className="px-2 py-2 text-center">{orden.tiempo_real_dias}</td>
                            <td className="px-2 py-2">
                              <span className={`px-2 py-1 rounded text-xs font-bold ${
                                orden.evaluacion === 'A tiempo' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                              }`}>
                                {orden.evaluacion}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-sm text-gray-500">No hay historial de órdenes para evaluar.</p>
                )}
              </div>
            )}
          </div>
        ) : (
          <div className="bg-gray-50 rounded-lg border-2 border-dashed border-gray-300 h-full flex items-center justify-center text-gray-500 p-8 text-center">
            Selecciona un proveedor de la lista para ver su información detallada y la evaluación de sus tiempos de entrega.
          </div>
        )}
      </div>
    </div>
  );
}