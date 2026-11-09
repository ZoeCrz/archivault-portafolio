import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

import { loadMarketplacePublication } from '../src/services/marketplace.js';
import {
  marketplaceApiQuery,
  normalizeMarketplacePage,
  updateMarketplaceParams,
} from '../src/services/marketplaceFilters.js';

const marketplaceSource = readFileSync(new URL('../src/pages/private/Marketplace.jsx', import.meta.url), 'utf8');
const css = readFileSync(new URL('../src/index.css', import.meta.url), 'utf8');

test('construye la consulta del marketplace sólo con filtros admitidos', () => {
  const params = new URLSearchParams('q=figura&tipo=PIEZA&page=2&desconocido=valor');
  assert.equal(marketplaceApiQuery(params), 'q=figura&tipo=PIEZA&page=2');
});

test('cambiar un filtro reinicia página y elimina vacíos y defaults', () => {
  const params = new URLSearchParams('q=anterior&page=4&estado=ACTIVA');
  const changed = updateMarketplaceParams(params, {
    q: ' nueva búsqueda ',
    estado: '',
    orden: 'recientes',
  });
  assert.equal(changed.get('q'), 'nueva búsqueda');
  assert.equal(changed.has('estado'), false);
  assert.equal(changed.has('orden'), false);
  assert.equal(changed.has('page'), false);
});

test('navegar de página conserva los filtros', () => {
  const params = new URLSearchParams('q=figura&condicion=USADA&page=2');
  const changed = updateMarketplaceParams(params, { page: 3 });
  assert.equal(changed.toString(), 'q=figura&condicion=USADA&page=3');
});

test('el filtro de favoritos persiste en URL y reinicia la página', () => {
  const params = new URLSearchParams('tipo=COLECCION&page=3');
  const changed = updateMarketplaceParams(params, { favoritos: 'true' });
  assert.equal(changed.get('favoritos'), 'true');
  assert.equal(changed.get('tipo'), 'COLECCION');
  assert.equal(changed.has('page'), false);
  assert.match(marketplaceApiQuery(changed), /favoritos=true/);
});

test('normaliza una respuesta paginada y degrada payloads inesperados', () => {
  const publication = { id: 1, tipo: 'PIEZA', nombre: 'Figura' };
  assert.deepEqual(
    normalizeMarketplacePage({ count: 1, next: '/page/2', previous: null, results: [publication] }),
    { count: 1, next: '/page/2', previous: null, results: [publication] },
  );
  assert.deepEqual(normalizeMarketplacePage(null), {
    count: 0,
    next: null,
    previous: null,
    results: [],
  });
});

test('el detalle utiliza únicamente el endpoint enriquecido de publicación', async () => {
  const originalFetch = globalThis.fetch;
  const originalStorage = globalThis.localStorage;
  const requests = [];
  globalThis.localStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} };
  globalThis.fetch = async url => {
    requests.push(url);
    return new Response(JSON.stringify({
      id: 7,
      tipo: 'COLECCION',
      nombre: 'Colección Retro',
      imagen: [],
      vendedor: { id: 2, nombre: 'seller' },
    }), { status: 200, headers: { 'Content-Type': 'application/json' } });
  };
  try {
    const publication = await loadMarketplacePublication('https://api.example', 7);
    assert.equal(publication.nombre, 'Colección Retro');
    assert.deepEqual(requests, ['https://api.example/api/v1/marketplace/publicaciones/7/']);
  } finally {
    globalThis.fetch = originalFetch;
    globalThis.localStorage = originalStorage;
  }
});

test('la vista responsive conserva filtros, favoritos, ofertas y paginación', () => {
  assert.match(marketplaceSource, /layout-container--wide marketplace-page/);
  assert.match(marketplaceSource, /layout-sidebar marketplace-page__layout/);
  assert.match(marketplaceSource, /layout-grid marketplace-results-grid/);
  assert.match(marketplaceSource, /onChange=\{event => updateFilter\('favoritos'/);
  assert.match(marketplaceSource, /onClick=\{\(\) => handleOfferAction/);
  assert.match(marketplaceSource, /onClick=\{\(\) => goToPage\(currentPage - 1\)\}/);
  assert.match(marketplaceSource, /onClick=\{\(\) => goToPage\(currentPage \+ 1\)\}/);
  assert.match(css, /@media \(max-width: 1024px\)[\s\S]*?\.marketplace-filters/);
  assert.match(css, /\.marketplace-pagination[\s\S]*?flex-wrap: wrap/);
});
