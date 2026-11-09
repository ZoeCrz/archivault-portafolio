import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const css = readFileSync(new URL('../src/index.css', import.meta.url), 'utf8');
const privateLayout = readFileSync(new URL('../src/components/layouts/PrivateLayout.jsx', import.meta.url), 'utf8');
const marketplace = readFileSync(new URL('../src/pages/private/Marketplace.jsx', import.meta.url), 'utf8');
const collections = readFileSync(new URL('../src/pages/private/MisColecciones.jsx', import.meta.url), 'utf8');
const collectionDetail = readFileSync(new URL('../src/pages/private/DetalleColeccion.jsx', import.meta.url), 'utf8');

test('notificaciones y chat usan contenedores limitados por viewport', () => {
  assert.match(css, /\.notification-popover[\s\S]*?width: min\(340px, calc\(100vw - 32px\)\)/);
  assert.match(css, /\.notification-popover__list[\s\S]*?overflow-y: auto/);
  assert.match(css, /\.chat-popover[\s\S]*?width: min\(350px, calc\(100vw - 48px\)\)/);
  assert.match(css, /height: min\(450px, calc\(100dvh - 48px\)\)/);
  assert.match(css, /@media \(max-width: 480px\)[\s\S]*?\.chat-popover \{ inset: 12px/);
});

test('la base modal ofrece scroll, separación segura y adaptación de columnas', () => {
  assert.match(css, /\.overlay-backdrop[\s\S]*?overflow-y: auto/);
  assert.match(css, /\.overlay-panel[\s\S]*?max-height: calc\(100dvh/);
  assert.match(css, /\.overlay-panel[\s\S]*?overflow-y: auto/);
  assert.match(css, /@media \(max-width: 768px\)[\s\S]*?\.overlay-panel--split/);
  assert.match(css, /\.overlay-close[\s\S]*?var\(--touch-target\)/);
});

test('los overlays conservan callbacks y contratos funcionales en PrivateLayout', () => {
  assert.match(privateLayout, /onNotificationsToggle=\{handleNotificationToggle\}/);
  assert.match(privateLayout, /onClick=\{\(\) => handlePersistentNotification\(notif\)\}/);
  assert.match(privateLayout, /onClick=\{handleMarkAllNotificationsRead\}/);
  assert.match(privateLayout, /onClick=\{handleSendMessage\}/);
  assert.match(privateLayout, /onClick=\{\(\) => navigate\('\/app\/marketplace'\)\}/);
  assert.match(privateLayout, /Outlet context=\{\{ addNotification, openChatWithUser, chatRouteStatus \}\}/);
});

test('los modales existentes adoptan la base sin cambiar sus acciones', () => {
  for (const source of [marketplace, collections, collectionDetail]) {
    assert.match(source, /overlay-backdrop/);
    assert.match(source, /overlay-panel/);
  }
  assert.match(marketplace, /onClick=\{handleCrearOferta\}/);
  assert.match(collections, /onClick=\{handleSaveCollection\}/);
  assert.match(collections, /onClick=\{handleDeleteConfirm\}/);
  assert.match(collectionDetail, /onClick=\{handleEditarPieza\}/);
  assert.match(collectionDetail, /onClick=\{handleDeletePiezaConfirm\}/);
});
