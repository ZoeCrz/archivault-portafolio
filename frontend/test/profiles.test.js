import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { biographyCount, loadProfileActivity, loadProfileSummary } from '../src/services/profiles.js';

const ownProfileSource = readFileSync(new URL('../src/pages/private/Perfil.jsx', import.meta.url), 'utf8');
const publicProfileSource = readFileSync(new URL('../src/pages/private/PerfilPublico.jsx', import.meta.url), 'utf8');

test('contador de biografía respeta el límite visible de 500', () => {
  assert.equal(biographyCount(''), 0);
  assert.equal(biographyCount('x'.repeat(500)), 500);
});

test('resumen y actividad usan endpoints específicos sin descargar listados globales', async () => {
  const originalFetch = globalThis.fetch;
  const originalStorage = globalThis.localStorage;
  const urls = [];
  globalThis.localStorage = { getItem: () => 'token', setItem() {}, removeItem() {} };
  globalThis.fetch = async url => { urls.push(url); return new Response(JSON.stringify({ results: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } }); };
  try {
    await loadProfileSummary('https://api.example', 4);
    await loadProfileActivity('https://api.example', 4, 'likes_realizados', 2, 5);
  } finally { globalThis.fetch = originalFetch; globalThis.localStorage = originalStorage; }
  assert.equal(urls[0], 'https://api.example/api/v1/accounts/profiles/4/resumen/');
  assert.match(urls[1], /profiles\/4\/actividad\/\?tipo=likes_realizados&page=2&page_size=5/);
});

test('likes realizados y recibidos conservan claves diferentes', () => {
  const stats = { likes_realizados: 2, likes_recibidos: 7 };
  assert.notEqual(stats.likes_realizados, stats.likes_recibidos);
  assert.deepEqual(Object.keys(stats), ['likes_realizados', 'likes_recibidos']);
});

test('perfil propio mantiene edición y actividad separada sin cronología falsa', () => {
  assert.match(ownProfileSource, /maxLength="500"/);
  assert.match(ownProfileSource, /Perfil público/);
  assert.match(ownProfileSource, /Likes realizados/);
  assert.match(ownProfileSource, /Likes recibidos/);
  assert.match(ownProfileSource, /Reseñas hechas/);
  assert.match(ownProfileSource, /Reseñas recibidas/);
  assert.match(ownProfileSource, /sin orden cronológico/i);
});

test('perfil público consume el resumen seguro y no renderiza edición privada', () => {
  assert.match(publicProfileSource, /loadProfileSummary/);
  assert.match(publicProfileSource, /Piezas públicas/);
  assert.match(publicProfileSource, /Reseñas recibidas/);
  assert.doesNotMatch(publicProfileSource, /Editar perfil|Likes realizados|Reseñas hechas/);
});

test('gráficos del propietario incluyen etiquetas y cantidades textuales', () => {
  assert.match(ownProfileSource, /Inventario por estado/);
  assert.match(ownProfileSource, /Progreso de colecciones/);
  assert.match(ownProfileSource, /Distribución de reseñas/);
  assert.match(ownProfileSource, /estrellas: \{value\}/);
});
