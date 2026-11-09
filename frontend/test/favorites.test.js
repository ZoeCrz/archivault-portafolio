import test from 'node:test';
import assert from 'node:assert/strict';

import {
  FAVORITE_TARGETS,
  createFavorite,
  deleteFavorite,
  favoritePayload,
  indexFavorites,
} from '../src/services/favorites.js';

test('construye payloads exclusivamente para pieza o colección maestra', () => {
  assert.deepEqual(favoritePayload(FAVORITE_TARGETS.PIECE, 4), { pieza_inventario: 4 });
  assert.deepEqual(favoritePayload(FAVORITE_TARGETS.COLLECTION, 8), { coleccion_maestra: 8 });
  assert.throws(() => favoritePayload('PUBLICACION', 2), /target type/);
  assert.throws(() => favoritePayload(FAVORITE_TARGETS.PIECE, 0), /target id/);
});

test('indexa piezas y colecciones por su objetivo estable', () => {
  const indexed = indexFavorites([
    { id: 1, tipo: 'PIEZA', objetivo_id: 5 },
    { id: 2, tipo: 'COLECCION', objetivo_id: 9 },
  ]);
  assert.equal(indexed.pieces.get(5).id, 1);
  assert.equal(indexed.collections.get(9).id, 2);
});

test('crea y elimina favoritos mediante el contrato centralizado', async () => {
  const originalFetch = globalThis.fetch;
  const originalStorage = globalThis.localStorage;
  const requests = [];
  globalThis.localStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} };
  globalThis.fetch = async (url, options = {}) => {
    requests.push({ url, options });
    if (options.method === 'DELETE') return new Response(null, { status: 204 });
    return new Response(JSON.stringify({ id: 12, tipo: 'COLECCION', objetivo_id: 7 }), {
      status: 201,
      headers: { 'Content-Type': 'application/json' },
    });
  };
  try {
    const favorite = await createFavorite('https://api.example', FAVORITE_TARGETS.COLLECTION, 7);
    await deleteFavorite('https://api.example', favorite.id, FAVORITE_TARGETS.COLLECTION, 7);
    assert.deepEqual(JSON.parse(requests[0].options.body), { coleccion_maestra: 7 });
    assert.equal(requests[1].url, 'https://api.example/api/v1/catalog/favoritos/12/');
    assert.equal(requests[1].options.method, 'DELETE');
  } finally {
    globalThis.fetch = originalFetch;
    globalThis.localStorage = originalStorage;
  }
});

test('un conflicto recupera el favorito existente sin duplicarlo', async () => {
  const originalFetch = globalThis.fetch;
  const originalStorage = globalThis.localStorage;
  let requestCount = 0;
  globalThis.localStorage = { getItem: () => null, setItem: () => {}, removeItem: () => {} };
  globalThis.fetch = async (url, options = {}) => {
    requestCount += 1;
    if (options.method === 'POST') {
      return new Response(JSON.stringify({ error: { code: 'conflict', message: 'Ya existe.' } }), {
        status: 409,
        headers: { 'Content-Type': 'application/json' },
      });
    }
    return new Response(JSON.stringify([
      { id: 21, tipo: 'PIEZA', objetivo_id: 3, pieza_inventario: 3 },
    ]), { status: 200, headers: { 'Content-Type': 'application/json' } });
  };
  try {
    const favorite = await createFavorite('https://api.example', FAVORITE_TARGETS.PIECE, 3);
    assert.equal(favorite.id, 21);
    assert.equal(requestCount, 2);
  } finally {
    globalThis.fetch = originalFetch;
    globalThis.localStorage = originalStorage;
  }
});
