import { apiRequest } from './api.js';

export function loadProfileSummary(apiUrl, profileId) {
  return apiRequest(`${apiUrl}/api/v1/accounts/profiles/${profileId}/resumen/`);
}

export function loadProfileActivity(apiUrl, profileId, type, page = 1, pageSize = 5) {
  const params = new URLSearchParams({ tipo: type, page: String(page), page_size: String(pageSize) });
  return apiRequest(`${apiUrl}/api/v1/accounts/profiles/${profileId}/actividad/?${params}`);
}

export function biographyCount(value) {
  return String(value || '').length;
}
