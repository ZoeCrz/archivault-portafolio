import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

import {
  AUTHENTICATED_PUBLIC_FOOTER_GROUPS,
  PRIVATE_BRAND_PATH,
  PRIVATE_FOOTER_GROUPS,
  PRIVATE_NAVIGATION,
  PUBLIC_BRAND_PATH,
  PUBLIC_FOOTER_GROUPS,
  PUBLIC_NAVIGATION,
  isNavigationItemActive,
} from '../src/components/navigation/navigationConfig.js';
import { clearSession } from '../src/services/api.js';

const headerSource = readFileSync(new URL('../src/components/navigation/SiteHeader.jsx', import.meta.url), 'utf8');
const primaryNavigationSource = readFileSync(new URL('../src/components/navigation/PrimaryNavigation.jsx', import.meta.url), 'utf8');
const privateLayoutSource = readFileSync(new URL('../src/components/layouts/PrivateLayout.jsx', import.meta.url), 'utf8');
const publicLayoutSource = readFileSync(new URL('../src/components/layouts/PublicLayout.jsx', import.meta.url), 'utf8');
const publicActionsSource = readFileSync(new URL('../src/components/navigation/PublicHeaderActions.jsx', import.meta.url), 'utf8');
const footerSource = readFileSync(new URL('../src/components/navigation/SiteFooter.jsx', import.meta.url), 'utf8');

const EXISTING_PUBLIC_ROUTES = new Set([
  '/',
  '/login',
  '/crear-cuenta',
  '/ayuda',
  '/privacidad',
  '/terminos',
  '/contacto',
]);
const EXISTING_PRIVATE_ROOTS = [
  '/app/colecciones',
  '/app/marketplace',
  '/app/comunidad',
  '/app/nueva-pieza',
  '/app/perfil',
];

test('las marcas pública y privada apuntan a sus destinos reales', () => {
  assert.equal(PUBLIC_BRAND_PATH, '/');
  assert.equal(PRIVATE_BRAND_PATH, '/app/colecciones');
});

test('la navegación pública sólo anuncia funciones públicas existentes', () => {
  assert.deepEqual(PUBLIC_NAVIGATION, [{ label: 'Inicio', to: '/', exact: true }]);
  for (const group of PUBLIC_FOOTER_GROUPS) {
    for (const link of group.links) assert.ok(EXISTING_PUBLIC_ROUTES.has(link.to));
  }
  const publicText = JSON.stringify({ navigation: PUBLIC_NAVIGATION, footer: PUBLIC_FOOTER_GROUPS });
  assert.doesNotMatch(publicText, /notificaci|logout|configuración|colecciones destacadas/i);
});

test('la navegación pública autenticada reemplaza login y registro por un retorno privado', () => {
  const links = AUTHENTICATED_PUBLIC_FOOTER_GROUPS.flatMap(group => group.links.map(link => link.to));
  assert.ok(links.includes('/app/colecciones'));
  assert.ok(!links.includes('/login'));
  assert.ok(!links.includes('/crear-cuenta'));
  assert.match(publicLayoutSource, /hasStoredSession \? AUTHENTICATED_PUBLIC_FOOTER_GROUPS : PUBLIC_FOOTER_GROUPS/);
  assert.match(publicActionsSource, /isAuthenticated/);
  assert.match(publicActionsSource, /Volver a mi bóveda/);
});

test('acciones y footer públicos exponen estado activo con NavLink', () => {
  assert.match(publicActionsSource, /<NavLink to="\/login"/);
  assert.match(publicActionsSource, /<NavLink to="\/crear-cuenta"/);
  assert.match(footerSource, /<NavLink to=\{link\.to\} end>/);
});

test('la navegación y footer privados sólo utilizan secciones implementadas', () => {
  const links = [
    ...PRIVATE_NAVIGATION.map(item => item.to),
    ...PRIVATE_FOOTER_GROUPS.flatMap(group => group.links.map(link => link.to)),
  ];
  for (const link of links) {
    assert.ok(
      EXISTING_PUBLIC_ROUTES.has(link)
      || EXISTING_PRIVATE_ROOTS.some(root => link === root || link.startsWith(`${root}/`)),
    );
  }
});

test('activa colecciones en lista y detalle, pero no en nueva pieza', () => {
  const collections = PRIVATE_NAVIGATION.find(item => item.to === '/app/colecciones');
  assert.equal(isNavigationItemActive(collections, '/app/colecciones'), true);
  assert.equal(isNavigationItemActive(collections, '/app/colecciones/12'), true);
  assert.equal(isNavigationItemActive(collections, '/app/nueva-pieza'), false);
});

test('activa marketplace y comunidad en lista y detalle', () => {
  const marketplace = PRIVATE_NAVIGATION.find(item => item.to === '/app/marketplace');
  const community = PRIVATE_NAVIGATION.find(item => item.to === '/app/comunidad');
  assert.equal(isNavigationItemActive(marketplace, '/app/marketplace'), true);
  assert.equal(isNavigationItemActive(marketplace, '/app/marketplace/publicaciones/3'), true);
  assert.equal(isNavigationItemActive(community, '/app/comunidad'), true);
  assert.equal(isNavigationItemActive(community, '/app/comunidad/publicaciones/7'), true);
});

test('Nueva Pieza sólo se activa en su ruta exacta', () => {
  const newPiece = PRIVATE_NAVIGATION.find(item => item.to === '/app/nueva-pieza');
  assert.equal(isNavigationItemActive(newPiece, '/app/nueva-pieza'), true);
  assert.equal(isNavigationItemActive(newPiece, '/app/nueva-pieza/otro'), false);
});

test('clearSession conserva el contrato utilizado por logout', () => {
  const removed = [];
  const originalLocalStorage = globalThis.localStorage;
  globalThis.localStorage = { removeItem: key => removed.push(key) };
  try {
    clearSession();
  } finally {
    globalThis.localStorage = originalLocalStorage;
  }
  assert.deepEqual(removed, [
    'archivault_access_token',
    'archivault_refresh_token',
    'archivault_user',
    'archivault_user_id',
  ]);
});

test('el header móvil expone controles accesibles sin asumir autenticación', () => {
  assert.match(headerSource, /aria-controls=\{navigationId\}/);
  assert.match(headerSource, /aria-expanded=\{menuOpen\}/);
  assert.match(headerSource, /Abrir menú de navegación/);
  assert.match(headerSource, /event\.key === 'Escape'/);
  assert.doesNotMatch(headerSource, /clearSession|localStorage|notification|chat|apiRequest/);
});

test('la navegación mantiene aria-current y cierra el menú al navegar', () => {
  assert.match(primaryNavigationSource, /aria-current=\{active \? 'page'/);
  assert.match(primaryNavigationSource, /onClick=\{onNavigate\}/);
});

test('la lógica privada y el contrato del Outlet permanecen en PrivateLayout', () => {
  assert.match(privateLayoutSource, /clearSession\(\)/);
  assert.match(privateLayoutSource, /handleSearchSubmit/);
  assert.match(privateLayoutSource, /notificationPanel/);
  assert.match(privateLayoutSource, /chatState\.open/);
  assert.match(privateLayoutSource, /Outlet context=\{\{ addNotification, openChatWithUser, chatRouteStatus \}\}/);
  assert.match(publicLayoutSource, /<Outlet \/>/);
});
