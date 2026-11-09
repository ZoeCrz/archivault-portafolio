import { apiRequest } from './api.js';

export async function loadMarketplacePublication(apiUrl, publicationId) {
  return apiRequest(`${apiUrl}/api/v1/marketplace/publicaciones/${publicationId}/`);
}
