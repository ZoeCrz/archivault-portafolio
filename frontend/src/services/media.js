const ABSOLUTE_WEB_URL = /^https?:\/\//i;
const SAFE_LOCAL_URL = /^(blob:|data:image\/)/i;
const URL_SCHEME = /^[a-z][a-z\d+.-]*:/i;

function getApiOrigin(apiBaseUrl) {
  if (!apiBaseUrl || !ABSOLUTE_WEB_URL.test(apiBaseUrl.trim())) return null;
  try {
    return new URL(apiBaseUrl.trim()).origin;
  } catch {
    return null;
  }
}

export function resolveMediaUrl(value, apiBaseUrl = import.meta.env.VITE_API_URL) {
  if (typeof value !== 'string') return null;
  const source = value.trim();
  if (!source) return null;

  if (ABSOLUTE_WEB_URL.test(source) || SAFE_LOCAL_URL.test(source)) return source;
  if (URL_SCHEME.test(source) || source.startsWith('//')) return null;

  const apiOrigin = getApiOrigin(apiBaseUrl);
  if (!apiOrigin) return null;

  const normalizedPath = source.startsWith('/')
    ? source
    : source.startsWith('media/')
      ? `/${source}`
      : `/media/${source}`;

  try {
    return new URL(normalizedPath, apiOrigin).href;
  } catch {
    return null;
  }
}

export function resolveMediaSources(values, apiBaseUrl = import.meta.env.VITE_API_URL) {
  const candidates = Array.isArray(values) ? values : [values];
  return [...new Set(
    candidates
      .map(value => resolveMediaUrl(value, apiBaseUrl))
      .filter(Boolean),
  )];
}
