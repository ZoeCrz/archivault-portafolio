import { apiRequest } from './api.js';
import { resourceRoutes } from './routes.js';

const DESTINATION_BUILDERS = {
  COMMUNITY_POST: resourceRoutes.communityPost,
  CHAT: resourceRoutes.chat,
  MARKETPLACE_PUBLICATION: resourceRoutes.marketplacePublication,
};

export function notificationDestination(notification) {
  const destination = notification?.destino;
  const build = DESTINATION_BUILDERS[destination?.tipo];
  const id = Number(destination?.id);
  if (!build || !Number.isSafeInteger(id) || id < 1) return null;
  return build(id);
}

export function normalizePersistentNotification(item) {
  return {
    id: item.id,
    mensaje: item.mensaje,
    tipo: item.tipo,
    evento: item.evento,
    destino: item.destino || null,
    leida: Boolean(item.leido),
    local: false,
    fecha: item.fecha,
  };
}

export async function loadPersistentNotifications(apiUrl) {
  const data = await apiRequest(`${apiUrl}/api/v1/webhooks/notificaciones/`);
  const items = Array.isArray(data) ? data : data.results || [];
  return items.map(normalizePersistentNotification);
}

export function markNotificationRead(apiUrl, id) {
  return apiRequest(`${apiUrl}/api/v1/webhooks/notificaciones/${id}/marcar-leida/`, {
    method: 'POST',
  });
}

export function markAllNotificationsRead(apiUrl) {
  return apiRequest(`${apiUrl}/api/v1/webhooks/notificaciones/marcar-leidas/`, {
    method: 'POST',
  });
}
