import test from 'node:test';
import assert from 'node:assert/strict';

import {
  buildPublicationPayload,
  createEmptySaleData,
  createMarketplacePublication,
  createSaleFormState,
  hasSaleErrors,
  saleFieldErrorsFrom,
  saleFormReducer,
  validateSaleData,
} from '../src/services/publications.js';

const validData = {
  precio: '125.50',
  condicion: 'USADA',
  descripcion: '  Conservada en funda.  ',
};

test('crea estado vacío para colección y precarga una condición válida para pieza', () => {
  assert.deepEqual(createEmptySaleData(), { precio: '', condicion: '', descripcion: '' });
  assert.deepEqual(createEmptySaleData('DAÑADA'), { precio: '', condicion: 'DAÑADA', descripcion: '' });
  assert.equal(createEmptySaleData('NO_ESPECIFICADA').condicion, '');
});

test('construye payload mínimo de pieza y recorta la descripción', () => {
  assert.deepEqual(buildPublicationPayload({ targetType: 'piece', targetId: 8, data: validData }), {
    pieza_inventario: 8,
    precio: '125.50',
    condicion: 'USADA',
    descripcion: 'Conservada en funda.',
  });
});

test('construye payload mínimo de colección y excluye campos no permitidos', () => {
  const payload = buildPublicationPayload({
    targetType: 'collection',
    targetId: 4,
    data: { ...validData, vendedor: 1, estado: 'VENDIDA', userId: 2 },
  });
  assert.deepEqual(payload, {
    coleccion_usuario: 4,
    precio: '125.50',
    condicion: 'USADA',
    descripcion: 'Conservada en funda.',
  });
});

test('valida precio obligatorio, numérico y mayor que cero', () => {
  for (const precio of ['', 'texto', '0', '-1']) {
    assert.ok(validateSaleData({ ...validData, precio }).precio, precio);
  }
  assert.equal(validateSaleData(validData).precio, undefined);
});

test('valida descripción vacía, espacios y longitud máxima', () => {
  for (const descripcion of ['', '   ', 'x'.repeat(501)]) {
    assert.ok(validateSaleData({ ...validData, descripcion }).descripcion);
  }
  assert.equal(validateSaleData(validData).descripcion, undefined);
});

test('rechaza condición vacía, desconocida o histórica', () => {
  for (const condicion of ['', 'MINT', 'NO_ESPECIFICADA']) {
    assert.ok(validateSaleData({ ...validData, condicion }).condicion);
  }
  assert.throws(
    () => buildPublicationPayload({
      targetType: 'piece',
      targetId: 1,
      data: { ...validData, condicion: 'NO_ESPECIFICADA' },
    }),
    /condition/,
  );
});

test('conserva únicamente errores backend correspondientes al formulario', () => {
  const errors = saleFieldErrorsFrom({
    fieldErrors: {
      precio: ['Precio inválido.'],
      descripcion: ['Descripción inválida.'],
      pieza_inventario: ['Pieza duplicada.'],
    },
  });
  assert.deepEqual(errors, {
    precio: ['Precio inválido.'],
    descripcion: ['Descripción inválida.'],
  });
});

test('el reducer impide un segundo inicio y cancelar limpia envío, datos y errores', () => {
  let state = createSaleFormState('NUEVA');
  state = saleFormReducer(state, { type: 'change', field: 'precio', value: '10' });
  state = saleFormReducer(state, { type: 'errors', errors: { descripcion: ['Requerida.'] } });
  state = saleFormReducer(state, { type: 'submit' });
  const repeated = saleFormReducer(state, { type: 'submit' });
  assert.equal(repeated, state);
  assert.equal(repeated.submitting, true);

  const reset = saleFormReducer(repeated, { type: 'cancel', initialCondition: '' });
  assert.deepEqual(reset, createSaleFormState(''));
  assert.equal(hasSaleErrors(reset.fieldErrors), false);
});

test('los tres puntos de entrada usan peticiones semánticamente equivalentes', async () => {
  const originalFetch = globalThis.fetch;
  const originalStorage = globalThis.localStorage;
  const requests = [];
  globalThis.localStorage = {
    getItem: () => null,
    setItem: () => {},
    removeItem: () => {},
  };
  globalThis.fetch = async (url, options) => {
    requests.push({ url, options, body: JSON.parse(options.body) });
    return new Response(JSON.stringify({ id: requests.length }), {
      status: 201,
      headers: { 'Content-Type': 'application/json' },
    });
  };
  try {
    await createMarketplacePublication('https://api.example', { targetType: 'piece', targetId: 1, data: validData });
    await createMarketplacePublication('https://api.example', { targetType: 'piece', targetId: 2, data: validData });
    await createMarketplacePublication('https://api.example', { targetType: 'collection', targetId: 3, data: validData });
  } finally {
    globalThis.fetch = originalFetch;
    globalThis.localStorage = originalStorage;
  }

  assert.equal(requests.length, 3);
  assert.ok(requests.every(request => request.options.method === 'POST'));
  assert.deepEqual(Object.keys(requests[0].body).sort(), ['condicion', 'descripcion', 'pieza_inventario', 'precio']);
  assert.deepEqual(Object.keys(requests[1].body).sort(), ['condicion', 'descripcion', 'pieza_inventario', 'precio']);
  assert.deepEqual(Object.keys(requests[2].body).sort(), ['coleccion_usuario', 'condicion', 'descripcion', 'precio']);
});

test('cancelar mediante reset no ejecuta ninguna petición', () => {
  let requestCount = 0;
  const state = saleFormReducer(createSaleFormState('USADA'), { type: 'cancel', initialCondition: '' });
  assert.equal(requestCount, 0);
  assert.deepEqual(state, createSaleFormState(''));
});

test('el éxito limpia el estado conservando la condición inicial indicada', () => {
  const dirty = {
    data: validData,
    fieldErrors: { precio: ['Error anterior.'] },
    submitting: true,
  };
  const state = saleFormReducer(dirty, { type: 'success', initialCondition: 'NUEVA' });
  assert.deepEqual(state, createSaleFormState('NUEVA'));
});
