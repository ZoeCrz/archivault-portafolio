import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

import { loadCommunitySummary, normalizeCommunitySummary } from '../src/services/community.js';

const communitySource = readFileSync(new URL('../src/pages/private/Comunidad.jsx', import.meta.url), 'utf8');
const css = readFileSync(new URL('../src/index.css', import.meta.url), 'utf8');

test('normaliza y limita ambas tarjetas a cinco elementos', () => {
  const payload = {
    novedades_marketplace: Array.from({ length: 7 }, (_, id) => ({ id, nombre: `Novedad ${id}` })),
    coleccionistas_top: Array.from({ length: 6 }, (_, id) => ({ id, nombre: `Usuario ${id}`, score: 6 - id })),
  };
  const summary = normalizeCommunitySummary(payload);
  assert.equal(summary.novedadesMarketplace.length, 5);
  assert.equal(summary.coleccionistasTop.length, 5);
  assert.equal(summary.novedadesMarketplace[0].nombre, 'Novedad 0');
  assert.equal(summary.coleccionistasTop[0].score, 6);
});

test('carga el resumen agregado desde un único endpoint', async () => {
  const originalFetch = globalThis.fetch;
  const originalStorage = globalThis.localStorage;
  const requests = [];
  globalThis.localStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} };
  globalThis.fetch = async url => {
    requests.push(url);
    return new Response(JSON.stringify({
      novedades_marketplace: [{ id: 1, nombre: 'Pieza real' }],
      coleccionistas_top: [{ id: 2, nombre: 'Coleccionista', score: 3 }],
    }), { status: 200, headers: { 'Content-Type': 'application/json' } });
  };
  try {
    const summary = await loadCommunitySummary('https://api.example');
    assert.equal(summary.novedades_marketplace[0].nombre, 'Pieza real');
    assert.deepEqual(requests, ['https://api.example/api/v1/community/resumen/']);
  } finally {
    globalThis.fetch = originalFetch;
    globalThis.localStorage = originalStorage;
  }
});

test('el layout responsive conserva publicación, comentarios, likes y multimedia', () => {
  assert.match(communitySource, /layout-container layout-container--wide community-layout/);
  assert.match(communitySource, /<form onSubmit=\{handlePublicar\}>/);
  assert.match(communitySource, /onClick=\{\(\) => handleLike\(post\.id\)\}/);
  assert.match(communitySource, /onClick=\{\(\) => handleComentar\(post\.id, post\.user\)\}/);
  assert.match(communitySource, /onChange=\{handleImageUpload\}/);
  assert.match(communitySource, /onChange=\{\(e\) => handleComentarioImageUpload\(e, post\.id\)\}/);
  assert.match(css, /\.community-layout[\s\S]*?grid-template-columns: minmax\(0, 1fr\) 320px/);
  assert.match(css, /@media \(max-width: 1024px\)[\s\S]*?\.community-layout \{ grid-template-columns: minmax\(0, 1fr\)/);
  assert.match(css, /@media \(max-width: 480px\)[\s\S]*?\.community-comment-form/);
});
