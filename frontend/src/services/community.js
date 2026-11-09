import { apiRequest } from './api.js';

export async function loadCommunitySummary(apiUrl) {
  return apiRequest(`${apiUrl}/api/v1/community/resumen/`);
}

export function normalizeCommunitySummary(payload) {
  return {
    novedadesMarketplace: Array.isArray(payload?.novedades_marketplace)
      ? payload.novedades_marketplace.slice(0, 5)
      : [],
    coleccionistasTop: Array.isArray(payload?.coleccionistas_top)
      ? payload.coleccionistas_top.slice(0, 5)
      : [],
  };
}
