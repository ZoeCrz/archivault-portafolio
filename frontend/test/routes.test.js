import test from 'node:test';
import assert from 'node:assert/strict';
import { DEFAULT_PRIVATE_PATH, getRequestedPath, resourceRoutes, safePrivateReturnPath } from '../src/services/routes.js';

test('conserva un deep link privado con query y hash', () => {
  const location = { pathname: '/app/colecciones/12', search: '?vista=grid', hash: '#pieza-4' };
  assert.equal(getRequestedPath(location), '/app/colecciones/12?vista=grid#pieza-4');
  assert.equal(safePrivateReturnPath(getRequestedPath(location)), '/app/colecciones/12?vista=grid#pieza-4');
});

test('rechaza destinos externos y rutas públicas como retorno', () => {
  assert.equal(safePrivateReturnPath('https://example.com/app/colecciones/1'), DEFAULT_PRIVATE_PATH);
  assert.equal(safePrivateReturnPath('//example.com/app/colecciones/1'), DEFAULT_PRIVATE_PATH);
  assert.equal(safePrivateReturnPath('/login'), DEFAULT_PRIVATE_PATH);
  assert.equal(safePrivateReturnPath('/application'), DEFAULT_PRIVATE_PATH);
  assert.equal(safePrivateReturnPath(null), DEFAULT_PRIVATE_PATH);
});

test('construye rutas estables con el identificador del recurso', () => {
  assert.equal(resourceRoutes.collection(12), '/app/colecciones/12');
  assert.equal(resourceRoutes.marketplacePublication(7), '/app/marketplace/publicaciones/7');
  assert.equal(resourceRoutes.communityPost(4), '/app/comunidad/publicaciones/4');
  assert.equal(resourceRoutes.profile(3), '/app/perfiles/3');
  assert.equal(resourceRoutes.chat(9), '/app/chats/9');
});
