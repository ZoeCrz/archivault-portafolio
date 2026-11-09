import {
  AppError,
  networkError,
  normalizeApiError,
  unexpectedResponseError,
} from './errors.js';

const API_URL = import.meta.env?.VITE_API_URL || 'http://localhost:8000';
const nativeFetch = (...args) => globalThis.fetch(...args);
let refreshInFlight = null;

export function isApiUrl(input) {
  try {
    const url = new URL(input instanceof Request ? input.url : input, globalThis.location?.href || API_URL);
    const base = new URL(API_URL);
    return url.origin === base.origin && !url.username && !url.password &&
      (url.pathname.startsWith('/api/v1/') || url.pathname === '/graphql/');
  } catch {
    return false;
  }
}

let redirectingToLogin = false;

export function clearSession() {
  localStorage.removeItem('archivault_access_token');
  localStorage.removeItem('archivault_refresh_token');
  localStorage.removeItem('archivault_user');
  localStorage.removeItem('archivault_user_id');
}

async function refreshAccessToken() {
  const refresh = localStorage.getItem('archivault_refresh_token');
  if (!refresh) return null;

  const response = await nativeFetch(`${API_URL}/api/v1/accounts/token/refresh/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  });

  if (!response.ok) return null;
  const data = await response.json().catch(() => null);
  if (!data?.access) return null;
  localStorage.setItem('archivault_access_token', data.access);
  if (data.refresh) localStorage.setItem('archivault_refresh_token', data.refresh);
  return data.access;
}

export async function apiFetch(url, options = {}) {
  // Only the configured API receives session credentials.
  if (!isApiUrl(url)) return nativeFetch(url, options);
  const headers = new Headers(options.headers || (url instanceof Request ? url.headers : {}));
  const access = localStorage.getItem('archivault_access_token');
  if (access) headers.set('Authorization', `Bearer ${access}`);

  let response = await nativeFetch(url, { ...options, headers });
  if (response.status !== 401) return response;

  if (!refreshInFlight) {
    refreshInFlight = refreshAccessToken().finally(() => { refreshInFlight = null; });
  }
  const renewedAccess = await refreshInFlight;
  if (!renewedAccess) {
    clearSession();
    if (!redirectingToLogin && window.location.pathname !== '/login') {
      redirectingToLogin = true;
      window.location.assign('/login');
    }
    return response;
  }

  headers.set('Authorization', `Bearer ${renewedAccess}`);
  response = await nativeFetch(url, { ...options, headers });
  return response;
}

async function parseResponseBody(response) {
  const text = await response.text();
  if (!text.trim()) return { data: null, empty: true, invalid: false };
  try {
    return { data: JSON.parse(text), empty: false, invalid: false };
  } catch {
    return { data: null, empty: false, invalid: true };
  }
}

export async function apiRequest(url, options = {}, { authenticated = true } = {}) {
  const method = options.method || 'GET';
  let response;
  try {
    response = authenticated
      ? await apiFetch(url, options)
      : await nativeFetch(url, options);
  } catch (cause) {
    throw networkError(cause, { url, method });
  }

  const parsed = await parseResponseBody(response);
  if (response.ok) {
    if (parsed.invalid) {
      throw unexpectedResponseError(response.status, { url, method, responseType: 'invalid_json' });
    }
    return parsed.data;
  }

  if (parsed.invalid) {
    throw unexpectedResponseError(response.status, { url, method, responseType: 'invalid_json' });
  }

  throw normalizeApiError({
    status: response.status,
    payload: parsed.data,
    requestId: response.headers.get('X-Request-ID'),
    technical: { url, method, responseType: parsed.empty ? 'empty' : 'json' },
  });
}

export function isAppError(error) {
  return error instanceof AppError;
}
