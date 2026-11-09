import test from 'node:test';
import assert from 'node:assert/strict';
import { apiFetch, isApiUrl } from '../src/services/api.js';

test('JWT is restricted to the configured API origin and paths', async () => {
  const oldFetch = globalThis.fetch;
  const oldStorage = globalThis.localStorage;
  globalThis.localStorage = { getItem: () => 'test-only-token' };
  const calls = [];
  globalThis.fetch = async (url, options) => {
    calls.push(new Headers(options.headers).get('Authorization'));
    return new Response(null, { status: 204 });
  };
  try {
    await apiFetch('https://external.invalid/resource');
    await apiFetch('http://localhost:8000/other');
    await apiFetch('http://localhost:8000/api/v1/accounts/users/');
    assert.deepEqual(calls, [null, null, 'Bearer test-only-token']);
    assert.equal(isApiUrl('http://localhost:8000.evil.invalid/api/v1/accounts/'), false);
    assert.equal(isApiUrl('http://user@localhost:8000/api/v1/accounts/'), false);
  } finally {
    globalThis.fetch = oldFetch;
    globalThis.localStorage = oldStorage;
  }
});
