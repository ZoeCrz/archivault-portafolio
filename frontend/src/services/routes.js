export const DEFAULT_PRIVATE_PATH = '/app/colecciones';

export function getRequestedPath(location) {
  return `${location.pathname || ''}${location.search || ''}${location.hash || ''}`;
}

export function safePrivateReturnPath(candidate, fallback = DEFAULT_PRIVATE_PATH) {
  if (typeof candidate !== 'string' || candidate.startsWith('//')) {
    return fallback;
  }

  try {
    const parsed = new URL(candidate, 'https://archivault.invalid');
    const isPrivatePath = parsed.pathname === '/app' || parsed.pathname.startsWith('/app/');
    if (parsed.origin !== 'https://archivault.invalid' || !isPrivatePath) {
      return fallback;
    }
    return `${parsed.pathname}${parsed.search}${parsed.hash}`;
  } catch {
    return fallback;
  }
}

export const resourceRoutes = {
  collection: id => `/app/colecciones/${id}`,
  marketplacePublication: id => `/app/marketplace/publicaciones/${id}`,
  communityPost: id => `/app/comunidad/publicaciones/${id}`,
  profile: id => `/app/perfiles/${id}`,
  chat: id => `/app/chats/${id}`,
};
