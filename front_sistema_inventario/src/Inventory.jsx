import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { all, amount, date, number } from './api'
import Icon from './Icons'
import InventoryForm from './InventoryForm'

const sections = [
  ['stock', 'box', 'Inventario'], ['catalog', 'grid', 'Catálogo de productos'],
  ['network', 'branch', 'Red de sucursales'], ['movements', 'swap', 'Movimientos'], ['alerts', 'alert', 'Reabastecimiento'],
]
const labels = { ADMIN_GENERAL: 'Administrador general', GERENTE_SUCURSAL: 'Gerente de sucursal', OPERADOR_INVENTARIO: 'Operador de inventario' }
const empty = { products: [], categories: [], branches: [], stocks: [], movements: [] }
export default function Inventory({ user, onLogout }) {
  const [section, setSection] = useState('stock')
  const [branchId, setBranchId] = useState(String(user.sucursal_id || ''))
  const [data, setData] = useState(empty)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [updated, setUpdated] = useState(null)
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('')
  const [status, setStatus] = useState('')
  const [page, setPage] = useState(1)
  const [modal, setModal] = useState(null)
  const [toast, setToast] = useState('')
  const [revision, setRevision] = useState(0)
  const [menuOpen, setMenuOpen] = useState(false)
  const requestId = useRef(0)
  const admin = user.rol.nombre === 'ADMIN_GENERAL'
  const operator = user.rol.nombre === 'OPERADOR_INVENTARIO'
  const branch = data.branches.find(b => String(b.id) === branchId)
  const local = admin || user.sucursal_id === Number(branchId)
  const editable = local && branch?.activa
  const manageMinimum = editable && !operator
  const canReadMovements = local && Boolean(branchId)
  const refresh = useCallback(async (signal) => {
    const current = ++requestId.current
    try {
      const [products, categories, branches, stocks, movements] = await Promise.all([
        all('/productos', signal), all('/categorias', signal), all('/sucursales', signal), all('/inventario', signal),
        section === 'movements' && branchId && (admin || user.sucursal_id === Number(branchId)) ? all(`/inventario/movimientos?sucursal_id=${branchId}`, signal) : Promise.resolve([]),
      ])
      if (signal.aborted || current !== requestId.current) return
      setData({ products, categories, branches, stocks, movements })
      if (!branchId && branches.length) setBranchId(String(branches[0].id))
      setError(''); setUpdated(new Date())
    } catch (e) {
      if (!signal.aborted && current === requestId.current) setError(e.message === 'Failed to fetch' ? 'No hay conexión con el servidor. Los datos pueden estar desactualizados.' : e.message)
    } finally { if (!signal.aborted && current === requestId.current) setLoading(false) }
  }, [admin, branchId, section, user.sucursal_id])
  useEffect(() => {
    const controller = new AbortController()
    let inFlight = false
    async function run() { if (inFlight) return; inFlight = true; await refresh(controller.signal); inFlight = false }
    run()
    const interval = setInterval(() => { if (!document.hidden) run() }, 15000)
    const focus = () => { if (!document.hidden) run() }
    document.addEventListener('visibilitychange', focus)
    return () => { controller.abort(); clearInterval(interval); document.removeEventListener('visibilitychange', focus) }
  }, [refresh, revision])
  useEffect(() => { if (!toast) return; const timeout = setTimeout(() => setToast(''), 6000); return () => clearTimeout(timeout) }, [toast])
  const productMap = useMemo(() => new Map(data.products.map(p => [p.id, p])), [data.products])
  const categoryMap = new Map(data.categories.map(c => [c.id, c.nombre]))
  const branchMap = new Map(data.branches.map(b => [b.id, b.nombre]))
  const localStocks = data.stocks.filter(s => String(s.sucursal_id) === branchId)
  const stockMap = new Map(localStocks.map(s => [s.producto_id, s]))
  const alerts = localStocks.filter(s => Number(s.stock_actual) <= Number(s.stock_minimo_local))
  const matches = product => product && (!category || String(product.categoria_id) === category) && `${product.sku} ${product.nombre} ${product.descripcion || ''}`.toLocaleLowerCase().includes(query.toLocaleLowerCase())
  const statusOf = stock => !stock ? 'none' : Number(stock.stock_actual) === 0 ? 'empty' : Number(stock.stock_actual) <= Number(stock.stock_minimo_local) ? 'low' : 'ok'
  let rows = section === 'catalog' ? data.products.map(p => ({ p, stock: stockMap.get(p.id), branch })) :
    (section === 'network' ? data.stocks : section === 'alerts' ? alerts : localStocks).map(s => ({ p: productMap.get(s.producto_id), stock: s, branch: data.branches.find(b => b.id === s.sucursal_id) }))
  rows = rows.filter(r => matches(r.p) && (!status || statusOf(r.stock) === status))
  const movements = (canReadMovements ? data.movements : []).filter(m => matches(productMap.get(m.producto_id)))
  const count = section === 'movements' ? movements.length : rows.length
  const pages = Math.max(1, Math.ceil(count / 10))
  const currentPage = Math.min(page, pages)
  const displayed = (section === 'movements' ? movements : rows).slice((currentPage - 1) * 10, currentPage * 10)
  function navigate(value) { setLoading(true); setRevision(x => x + 1); setSection(value); setQuery(''); setCategory(''); setStatus(''); setPage(1); setMenuOpen(false) }
  const open = (type, row = {}) => setModal({ type, product: row.p, stock: row.stock })
  const title = sections.find(x => x[0] === section)[2]
  const subtitles = { stock: 'Cada producto, cada unidad. Todo bajo control.', catalog: 'La información de tus productos, compartida por toda la red.', network: 'Consulta la disponibilidad de tecnología en todas tus sucursales.', movements: 'Un historial claro de cada entrada y salida de inventario.', alerts: 'Anticípate a los faltantes y mantén tus sucursales abastecidas.' }
  const badge = stock => {
    const s = statusOf(stock)
    return <span className={`badge ${s}`}>{ { none: 'Sin registro', empty: 'Agotado', low: 'Stock bajo', ok: 'Disponible' }[s]}</span>
  }
  return <div className="app-layout">
    <aside className={`sidebar ${menuOpen ? 'expanded' : ''}`}><a href="#" className="brand" onClick={e => { e.preventDefault(); navigate('stock') }}><span className="brand-mark"><Icon/></span>nodo<span className="brand-dot">.</span></a><span className="sidebar-caption">ESPACIO DE TRABAJO</span><nav aria-label="Navegación de inventario">{sections.map(([id, icon, label]) => <button key={id} className={section === id ? 'nav-item active' : 'nav-item'} onClick={() => navigate(id)} aria-current={section === id ? 'page' : undefined}><Icon name={icon}/><span>{label}</span>{id === 'alerts' && alerts.length > 0 && <span className="nav-count">{alerts.length}</span>}</button>)}</nav><div className="sidebar-bottom"><div className="network-note"><span className="live-dot"/>Una red. Todas tus sucursales.<small>Inventario tecnológico conectado.</small></div><div className="profile"><span className="avatar">{user.nombre.slice(0, 2).toUpperCase()}</span><div><strong>{user.nombre}</strong><small>{labels[user.rol.nombre]}</small></div><button className="icon-button" onClick={onLogout} aria-label="Cerrar sesión"><Icon name="logout" size={17}/></button></div></div></aside>
    <div className="workspace"><header className="topbar"><div className="breadcrumb"><button className="mobile-menu icon-button" onClick={() => setMenuOpen(!menuOpen)} aria-label="Abrir menú"><Icon name="grid"/></button><span>Gestión de inventario</span><span>/</span><strong>{title}</strong></div><div className="top-actions"><span className="top-role">{labels[user.rol.nombre]}</span><span className="avatar small">{user.nombre.slice(0, 2).toUpperCase()}</span></div></header>
    <main className="content"><div className="page-heading"><div><span className="section-kicker">TU OPERACIÓN, EN UN SOLO LUGAR</span><h1>{title}</h1><p>{subtitles[section]}</p></div><div className="heading-actions">{editable && <button className="secondary" onClick={() => open('move')} disabled={!data.products.length}><Icon name="swap" size={17}/>Registrar movimiento</button>}{operator && <button className="primary" onClick={() => open('create')} disabled={!local || !branch?.activa || !data.categories.length}><Icon name="plus" size={18}/>Nuevo producto</button>}</div></div>
    <div className="scope-bar"><label className="branch-select"><Icon name="branch"/><span>Sucursal</span><select aria-label="Sucursal consultada" value={branchId} onChange={e => { setLoading(true); setBranchId(e.target.value); setPage(1) }}><option value="" disabled>Seleccionar sucursal</option>{data.branches.map(b => <option key={b.id} value={b.id}>{b.nombre}{b.id === user.sucursal_id ? ' · Mi sucursal' : ''}{!b.activa ? ' · Inactiva' : ''}</option>)}</select></label><div className="sync"><span className={`live-dot ${error ? 'offline' : ''}`}/>{loading ? 'Actualizando…' : error ? 'Sin sincronizar' : `Actualizado ${updated?.toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' }) || ''}`}<button className="icon-button" title="Actualizar inventario" aria-label="Actualizar inventario" disabled={loading} onClick={() => { setLoading(true); setRevision(x => x + 1) }}><Icon name="refresh" size={17}/></button></div></div>
    {error && <div className="notice error" role="alert">{error}<button onClick={() => { setLoading(true); setRevision(x => x + 1) }}>Reintentar</button></div>}
    {!local && branch && section !== 'network' && <div className="notice"><Icon name="eye" size={17}/>Consulta de otra sucursal. Las operaciones se realizan en tu sucursal asignada.</div>}
    <section className="stats" aria-label="Resumen de la sucursal"><article><div className="stat-label">Productos en sucursal<Icon name="box"/></div><strong>{number(localStocks.length)}</strong><small>Referencias registradas</small></article><article><div className="stat-label">Con disponibilidad<Icon name="check"/></div><strong>{number(localStocks.filter(s => Number(s.stock_actual) > 0).length)}</strong><small>Productos con stock positivo</small></article><article className={alerts.length ? 'warning-stat' : ''}><div className="stat-label">Por reabastecer<Icon name="alert"/></div><strong>{number(alerts.length)}<span>productos</span></strong><button onClick={() => navigate('alerts')}>Ver alertas <Icon name="arrow" size={14}/></button></article><article><div className="stat-label">Valor del inventario<Icon name="grid"/></div><strong className="stat-money">{amount(localStocks.reduce((sum, s) => sum + Number(s.stock_actual) * Number(s.costo_promedio_ponderado), 0))}</strong><small>A costo promedio ponderado</small></article></section>
    <section className="table-panel"><div className="table-heading"><div><h2>{section === 'stock' ? 'Productos de la sucursal' : title}<span className="count-pill">{number(count)}</span></h2><p>{section === 'network' ? 'Stock visible en toda la red. Operaciones limitadas por rol.' : section === 'movements' ? 'Fecha, responsable, motivo y cantidad de cada operación.' : 'Información conectada directamente con tu inventario.'}</p></div>{admin && section === 'catalog' && <button className="text-button" onClick={() => open('category')}><Icon name="plus" size={16}/>Nueva categoría</button>}</div>
    <div className="filters"><div className="search"><Icon name="search" size={18}/><input aria-label="Buscar productos" placeholder="Buscar por nombre, SKU o descripción…" value={query} onChange={e => { setQuery(e.target.value); setPage(1) }}/>{query && <button className="icon-button" aria-label="Limpiar búsqueda" onClick={() => setQuery('')}><Icon name="close" size={14}/></button>}</div><select aria-label="Filtrar categoría" value={category} onChange={e => { setCategory(e.target.value); setPage(1) }}><option value="">Todas las categorías</option>{data.categories.map(c => <option key={c.id} value={c.id}>{c.nombre}</option>)}</select>{section !== 'movements' && <select aria-label="Filtrar estado de stock" value={status} onChange={e => { setStatus(e.target.value); setPage(1) }}><option value="">Todos los estados</option><option value="ok">Disponible</option><option value="low">Stock bajo</option><option value="empty">Agotado</option>{section === 'catalog' && <option value="none">Sin registro</option>}</select>}</div>
    {section === 'movements' && !canReadMovements ? <div className="empty-state"><Icon name="lock" size={32}/><h3>Historial de acceso restringido</h3><p>Puedes consultar el stock de otras sucursales. Su historial está disponible para sus responsables y el administrador.</p></div> : loading ? <div className="empty-state" role="status"><Icon name="refresh" size={28}/><h3>Consultando inventario…</h3></div> : !count ? <div className="empty-state"><div className="empty-icon"><Icon name={section === 'alerts' ? 'check' : 'box'} size={30}/></div><h3>{query || category || status ? 'No encontramos coincidencias' : section === 'alerts' ? 'Todo está bajo control' : section === 'movements' ? 'Aún no hay movimientos' : 'Tu inventario comienza aquí'}</h3><p>{query || category || status ? 'Prueba otra búsqueda o cambia los filtros.' : section === 'alerts' ? 'No hay productos en el umbral de reabastecimiento de esta sucursal.' : 'Los productos y sus movimientos aparecerán aquí cuando se registren.'}</p>{!data.categories.length && <p>Un administrador debe crear las categorías desde Catálogo de productos.</p>}{!data.branches.length && <p>Configura primero las sucursales y usuarios en el backend.</p>}{section === 'stock' && data.products.length > 0 && <button className="secondary" onClick={() => navigate('catalog')}>Explorar catálogo general<Icon name="arrow" size={16}/></button>}</div> : <div className="table-scroll"><table>{section === 'movements' ? <><thead><tr><th>Fecha y producto</th><th>Movimiento</th><th>Cantidad</th><th>Stock resultante</th><th>Responsable</th><th>Motivo</th></tr></thead><tbody>{displayed.map(m => <tr key={m.id}><td><strong>{productMap.get(m.producto_id)?.nombre || `Producto #${m.producto_id}`}</strong><small>{date(m.fecha_movimiento)}</small></td><td><span className={`badge ${m.tipo_movimiento === 'INGRESO' ? 'ok' : 'low'}`}>{m.tipo_movimiento === 'INGRESO' ? 'Entrada' : 'Salida'}</span></td><td className="quantity">{m.tipo_movimiento === 'INGRESO' ? '+' : '−'}{number(m.cantidad)}</td><td>{number(m.stock_resultante)}</td><td>{m.usuario_id === user.id ? user.nombre : m.usuario_id ? `Usuario #${m.usuario_id}` : 'Histórico sin responsable'}</td><td className="reason-cell">{m.motivo}</td></tr>)}</tbody></> : <><thead><tr><th>Producto</th><th>{section === 'network' ? 'Sucursal' : 'Categoría'}</th><th>Stock disponible</th><th>Mínimo</th><th>Estado</th><th className="right">Acciones</th></tr></thead><tbody>{displayed.map(row => <tr key={row.stock?.id || `p-${row.p.id}`}><td><button className="product-cell" onClick={() => open('view', row)}><span className="product-symbol"><Icon name="laptop" size={22}/></span><span><strong>{row.p.nombre}</strong><code>{row.p.sku}</code></span></button></td><td>{section === 'network' ? branchMap.get(row.stock.sucursal_id) : categoryMap.get(row.p.categoria_id)}</td><td><span className="quantity">{row.stock ? number(row.stock.stock_actual) : '—'}</span><small>{row.p.unidad_medida}</small></td><td>{row.stock ? number(row.stock.stock_minimo_local) : '—'}</td><td>{badge(row.stock)}</td><td><div className="row-actions"><button className="icon-button" onClick={() => open('view', row)} title="Ver detalle" aria-label={`Ver ${row.p.nombre}`}><Icon name="eye" size={17}/></button>{section !== 'network' && <>{admin && <button className="icon-button" onClick={() => open('edit', row)} title="Editar producto" aria-label={`Editar ${row.p.nombre}`}><Icon name="edit" size={17}/></button>}{manageMinimum && <button className="icon-button" onClick={() => open('minimum', row)} title="Configurar mínimo" aria-label={`Mínimo de ${row.p.nombre}`}><Icon name="alert" size={17}/></button>}{editable && <button className="icon-button" onClick={() => open('move', row)} title="Registrar movimiento" aria-label={`Movimiento de ${row.p.nombre}`}><Icon name="swap" size={17}/></button>}{admin && <button className="icon-button delete-action" onClick={() => open('delete', row)} title="Eliminar producto" aria-label={`Eliminar ${row.p.nombre}`}><Icon name="trash" size={17}/></button>}</>}</div></td></tr>)}</tbody></>}</table></div>}
    <div className="pagination"><span>{count ? `${(currentPage - 1) * 10 + 1}–${Math.min(currentPage * 10, count)} de ${number(count)} registros` : '0 registros'}</span><div><button disabled={currentPage <= 1} onClick={() => setPage(currentPage - 1)}>Anterior</button><span>{currentPage} / {pages}</span><button disabled={currentPage >= pages} onClick={() => setPage(currentPage + 1)}>Siguiente</button></div></div></section>
    <div className="page-footer"><span><Icon name="lock" size={13}/> Cada movimiento deja una huella auditable.</span><span>Actualización automática cada 15 segundos</span></div>
    </main></div>
    {toast && <div className="toast" role="status"><Icon name="check" size={19}/><span>{toast}</span><button className="icon-button" aria-label="Cerrar notificación" onClick={() => setToast('')}><Icon name="close" size={16}/></button></div>}
    {modal && <InventoryForm modal={modal} categories={data.categories} products={data.products} branch={modal.stock ? data.branches.find(b => b.id === modal.stock.sucursal_id) : branch} user={user} onClose={() => setModal(null)} onSaved={message => { setModal(null); setToast(message); setLoading(true); setRevision(x => x + 1) }}/ >}
  </div>
}
