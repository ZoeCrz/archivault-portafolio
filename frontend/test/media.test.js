import test from 'node:test';
import assert from 'node:assert/strict';

import { resolveMediaSources, resolveMediaUrl } from '../src/services/media.js';

const API_URL = 'https://api.example/base';

test('conserva URLs web absolutas y URLs externas históricas', () => {
  assert.equal(
    resolveMediaUrl('https://legacy.example/image.png', API_URL),
    'https://legacy.example/image.png',
  );
  assert.equal(
    resolveMediaUrl('http://legacy.example/image.png', API_URL),
    'http://legacy.example/image.png',
  );
});

test('resuelve /media y nombres relativos exclusivamente contra el backend', () => {
  assert.equal(
    resolveMediaUrl('/media/pieces/item.png', API_URL),
    'https://api.example/media/pieces/item.png',
  );
  assert.equal(
    resolveMediaUrl('pieces/item.png', API_URL),
    'https://api.example/media/pieces/item.png',
  );
  assert.equal(
    resolveMediaUrl('media/pieces/item.png', API_URL),
    'https://api.example/media/pieces/item.png',
  );
});

test('devuelve null para vacíos, tipos inválidos o falta de backend absoluto', () => {
  assert.equal(resolveMediaUrl(null, API_URL), null);
  assert.equal(resolveMediaUrl('', API_URL), null);
  assert.equal(resolveMediaUrl('pieces/item.png', ''), null);
  assert.equal(resolveMediaUrl('pieces/item.png', '/api'), null);
  assert.equal(resolveMediaUrl('javascript:alert(1)', API_URL), null);
  assert.equal(resolveMediaUrl('//unexpected.example/item.png', API_URL), null);
});

test('mantiene previews locales seguros', () => {
  assert.equal(resolveMediaUrl('blob:https://frontend.example/id', API_URL), 'blob:https://frontend.example/id');
  assert.equal(resolveMediaUrl('data:image/png;base64,abc', API_URL), 'data:image/png;base64,abc');
});

test('ordena archivo antes de URL histórica y elimina duplicados', () => {
  assert.deepEqual(
    resolveMediaSources(
      ['/media/pieces/item.png', 'https://legacy.example/item.png', '/media/pieces/item.png'],
      API_URL,
    ),
    ['https://api.example/media/pieces/item.png', 'https://legacy.example/item.png'],
  );
});
