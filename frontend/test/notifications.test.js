import test from 'node:test';
import assert from 'node:assert/strict';

import {
  loadPersistentNotifications,
  markAllNotificationsRead,
  markNotificationRead,
  normalizePersistentNotification,
  notificationDestination,
} from '../src/services/notifications.js';

test('resuelve únicamente destinos conocidos con IDs válidos', () => {
  assert.equal(
    notificationDestination({ destino: { tipo: 'COMMUNITY_POST', id: 4, url: 'https://evil.example' } }),
    '/app/comunidad/publicaciones/4',
  );
  assert.equal(notificationDestination({ destino: { tipo: 'CHAT', id: 8 } }), '/app/chats/8');
  assert.equal(
    notificationDestination({ destino: { tipo: 'MARKETPLACE_PUBLICATION', id: 3 } }),
    '/app/marketplace/publicaciones/3',
  );
  assert.equal(notificationDestination({ destino: { tipo: 'EXTERNAL_URL', id: 1, url: 'https://evil.example' } }), null);
  assert.equal(notificationDestination({ destino: { tipo: 'CHAT', id: '../login' } }), null);
  assert.equal(notificationDestination({ destino: null }), null);
});

test('normaliza una persistente y conserva destino y lectura durante polling', () => {
  const notification = normalizePersistentNotification({
    id: 2,
    tipo: 'mensaje',
    evento: 'CHAT_MESSAGE',
    mensaje: 'Nuevo mensaje',
    leido: true,
    fecha: '2026-08-17T00:00:00Z',
    destino: { tipo: 'CHAT', id: 7, url: '/app/chats/7' },
  });

  assert.equal(notification.local, false);
  assert.equal(notification.leida, true);
  assert.deepEqual(notification.destino, { tipo: 'CHAT', id: 7, url: '/app/chats/7' });
});

test('cargar no marca notificaciones y los marcados requieren llamadas explícitas', async () => {
  const originalFetch = globalThis.fetch;
  const originalLocalStorage = globalThis.localStorage;
  const calls = [];
  globalThis.localStorage = {
    getItem: () => 'test-access-token',
    setItem: () => {},
    removeItem: () => {},
  };
  globalThis.fetch = async (url, options = {}) => {
    calls.push({ url, method: options.method || 'GET' });
    return new Response(JSON.stringify([]), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  };
  try {
    await loadPersistentNotifications('https://api.example');
    assert.deepEqual(calls, [{
      url: 'https://api.example/api/v1/webhooks/notificaciones/',
      method: 'GET',
    }]);

    await markNotificationRead('https://api.example', 9);
    await markAllNotificationsRead('https://api.example');
    assert.deepEqual(calls.slice(1), [
      {
        url: 'https://api.example/api/v1/webhooks/notificaciones/9/marcar-leida/',
        method: 'POST',
      },
      {
        url: 'https://api.example/api/v1/webhooks/notificaciones/marcar-leidas/',
        method: 'POST',
      },
    ]);
  } finally {
    globalThis.fetch = originalFetch;
    globalThis.localStorage = originalLocalStorage;
  }
});
