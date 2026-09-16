const base = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '')
export const session = {
  get: () => sessionStorage.getItem('inventario.token'),
  set: token => sessionStorage.setItem('inventario.token', token),
  clear: () => sessionStorage.removeItem('inventario.token'),
}
export async function api(path, { method = 'GET', body, signal } = {}) {
  const token = session.get()
  const response = await fetch(`${base}/api${path}`, {
    method, signal,
    headers: { ...(body ? { 'Content-Type': 'application/json' } : {}), ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (response.status === 204) return null
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    if (response.status === 401 && path !== '/auth/login' && token === session.get()) {
      session.clear()
      window.dispatchEvent(new Event('session-expired'))
    }
    const detail = data.detail
    const message = Array.isArray(detail) ? detail.map(x => `${x.loc?.slice(1).join('.') || 'Datos'}: ${x.msg}`).join(' · ') : detail
    throw new Error(typeof message === 'string' ? message : `No se pudo completar la operación (${response.status}).`)
  }
  return data
}
export async function all(path, signal) {
  const result = []
  for (let offset = 0; ; offset += 200) {
    const page = await api(`${path}${path.includes('?') ? '&' : '?'}offset=${offset}&limit=200`, { signal })
    result.push(...page)
    if (page.length < 200) return result
  }
}
export const number = value => new Intl.NumberFormat('es-CO', { maximumFractionDigits: 3 }).format(Number(value || 0))
export const amount = value => new Intl.NumberFormat('es-CO', { maximumFractionDigits: 2 }).format(Number(value || 0))
export function date(value) {
  if (!value) return '—'
  const utc = /Z$|[+-]\d\d:\d\d$/.test(value) ? value : `${value}Z`
  return new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(utc))
}
