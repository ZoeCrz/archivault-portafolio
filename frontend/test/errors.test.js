import test from 'node:test';
import assert from 'node:assert/strict';

import {
  AppError,
  networkError,
  normalizeApiError,
  unexpectedResponseError,
} from '../src/services/errors.js';
import { apiRequest } from '../src/services/api.js';


test('normaliza el contrato nuevo y conserva campos públicos', () => {
  const error = normalizeApiError({
    status: 400,
    payload: {
      error: {
        code: 'validation_error',
        message: 'Revisa los datos indicados.',
        fields: { monto: ['Debe ser mayor que cero.'] },
        request_id: 'request-1',
      },
    },
  });

  assert.ok(error instanceof AppError);
  assert.equal(error.code, 'validation_error');
  assert.deepEqual(error.fieldErrors, { monto: ['Debe ser mayor que cero.'] });
  assert.equal(error.requestId, 'request-1');
});

test('mantiene compatibilidad temporal con errores antiguos por campo', () => {
  const error = normalizeApiError({
    status: 400,
    payload: { username: ['Este nombre ya existe.'], non_field_errors: ['Conflicto.'] },
  });

  assert.equal(error.userMessage, 'Revisa los datos indicados.');
  assert.deepEqual(error.fieldErrors.username, ['Este nombre ya existe.']);
  assert.deepEqual(error.fieldErrors.non_field_errors, ['Conflicto.']);
});

test('clasifica estados HTTP con mensajes diferentes y seguros', () => {
  const expected = {
    401: 'authentication_required',
    403: 'permission_denied',
    404: 'not_found',
    409: 'conflict',
    500: 'internal_error',
  };

  for (const [status, code] of Object.entries(expected)) {
    const error = normalizeApiError({ status: Number(status), payload: null });
    assert.equal(error.code, code);
    assert.ok(error.userMessage);
  }
});

test('no muestra payloads crudos de formatos antiguos', () => {
  const error = normalizeApiError({
    status: 500,
    payload: { detail: 'DatabaseError at internal-host:3306' },
  });

  assert.equal(error.code, 'internal_error');
  assert.doesNotMatch(error.userMessage, /DatabaseError|3306/);
});

test('clasifica HTML, JSON inválido y respuestas inesperadas sin exponer contenido', () => {
  for (const responseType of ['html', 'invalid_json']) {
    const error = unexpectedResponseError(502, { responseType });
    assert.equal(error.code, 'unexpected_response');
    assert.doesNotMatch(error.userMessage, /html|json/i);
  }
});

test('clasifica respuesta de error vacía por su estado', () => {
  const error = normalizeApiError({ status: 404, payload: null });
  assert.equal(error.code, 'not_found');
  assert.deepEqual(error.fieldErrors, {});
});

test('clasifica errores de red sin mostrar la excepción técnica', () => {
  const error = networkError(new TypeError('Failed to fetch internal-host'));
  assert.equal(error.code, 'network_error');
  assert.doesNotMatch(error.userMessage, /internal-host|Failed to fetch/);
  assert.ok(error.technical.cause instanceof TypeError);
});

test('apiRequest acepta una respuesta exitosa vacía', async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => new Response(null, { status: 204 });
  try {
    assert.equal(
      await apiRequest('https://api.example/empty', {}, { authenticated: false }),
      null,
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('apiRequest rechaza HTML o JSON inválido como respuesta inesperada', async () => {
  const originalFetch = globalThis.fetch;
  for (const body of ['<html>error interno</html>', '{json-incompleto']) {
    globalThis.fetch = async () => new Response(body, { status: 500 });
    await assert.rejects(
      apiRequest('https://api.example/error', {}, { authenticated: false }),
      error => error.code === 'unexpected_response' && !error.userMessage.includes(body),
    );
  }
  globalThis.fetch = originalFetch;
});

test('apiRequest convierte un rechazo de fetch en error de red', async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => { throw new TypeError('socket internal details'); };
  try {
    await assert.rejects(
      apiRequest('https://api.example/network', {}, { authenticated: false }),
      error => error.code === 'network_error' && !error.userMessage.includes('socket'),
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});
