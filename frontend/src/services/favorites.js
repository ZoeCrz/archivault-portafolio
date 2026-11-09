import { apiRequest } from './api.js';

export const FAVORITE_TARGETS = {
  PIECE: 'PIEZA',
  COLLECTION: 'COLECCION',
};

export function favoritePayload(targetType, targetId) {
  if (!Number.isInteger(Number(targetId)) || Number(targetId) <= 0) {
    throw new TypeError('favorite target id');
  }
  if (targetType === FAVORITE_TARGETS.PIECE) {
    return { pieza_inventario: Number(targetId) };
  }
  if (targetType === FAVORITE_TARGETS.COLLECTION) {
    return { coleccion_maestra: Number(targetId) };
  }
  throw new TypeError('favorite target type');
}

export async function listFavorites(apiUrl, targetType = null) {
  const suffix = targetType ? `?tipo=${encodeURIComponent(targetType)}` : '';
  const data = await apiRequest(`${apiUrl}/api/v1/catalog/favoritos/${suffix}`);
  return Array.isArray(data) ? data : data?.results || [];
}

export function indexFavorites(favorites) {
  const pieces = new Map();
  const collections = new Map();
  favorites.forEach(favorite => {
    const target = favorite.tipo === FAVORITE_TARGETS.PIECE ? pieces : collections;
    target.set(Number(favorite.objetivo_id), favorite);
  });
  return { pieces, collections };
}

export async function findFavorite(apiUrl, targetType, targetId) {
  const favorites = await listFavorites(apiUrl, targetType);
  return favorites.find(item => Number(item.objetivo_id) === Number(targetId)) || null;
}

export async function createFavorite(apiUrl, targetType, targetId) {
  try {
    return await apiRequest(`${apiUrl}/api/v1/catalog/favoritos/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(favoritePayload(targetType, targetId)),
    });
  } catch (error) {
    if (error?.code === 'conflict') {
      const existing = await findFavorite(apiUrl, targetType, targetId);
      if (existing) return existing;
    }
    throw error;
  }
}

export async function deleteFavorite(apiUrl, favoriteId, targetType, targetId) {
  let id = favoriteId;
  if (!id) id = (await findFavorite(apiUrl, targetType, targetId))?.id;
  if (!id) return false;
  await apiRequest(`${apiUrl}/api/v1/catalog/favoritos/${id}/`, { method: 'DELETE' });
  return true;
}
