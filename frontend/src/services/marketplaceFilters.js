export const MARKETPLACE_DEFAULT_ORDER = 'recientes';

export const MARKETPLACE_FILTER_KEYS = [
  'q',
  'tipo',
  'estado',
  'condicion',
  'categoria',
  'coleccion',
  'precio_min',
  'precio_max',
  'favoritos',
  'orden',
  'page',
];

export function updateMarketplaceParams(current, changes) {
  const next = new URLSearchParams(current);
  const changesPage = Object.keys(changes).some(key => key !== 'page');
  Object.entries(changes).forEach(([key, rawValue]) => {
    const value = typeof rawValue === 'string' ? rawValue.trim() : rawValue;
    const isDefault = key === 'orden' && value === MARKETPLACE_DEFAULT_ORDER;
    if (value === '' || value === null || value === undefined || isDefault) next.delete(key);
    else next.set(key, String(value));
  });
  if (changesPage) next.delete('page');
  return next;
}

export function marketplaceApiQuery(searchParams) {
  const query = new URLSearchParams();
  MARKETPLACE_FILTER_KEYS.forEach(key => {
    const value = searchParams.get(key);
    if (value) query.set(key, value);
  });
  return query.toString();
}

export function normalizeMarketplacePage(payload) {
  if (!payload || !Array.isArray(payload.results)) {
    return { count: 0, next: null, previous: null, results: [] };
  }
  return {
    count: Number(payload.count) || 0,
    next: payload.next || null,
    previous: payload.previous || null,
    results: payload.results,
  };
}
