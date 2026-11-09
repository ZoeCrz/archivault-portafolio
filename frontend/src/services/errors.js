export const USER_MESSAGES = {
  validation_error: 'Revisa los datos indicados.',
  authentication_required: 'Tu sesión ha expirado. Inicia sesión nuevamente.',
  invalid_credentials: 'El usuario o la contraseña no son correctos.',
  permission_denied: 'No tienes permiso para realizar esta acción.',
  not_found: 'El contenido solicitado ya no está disponible o no existe.',
  conflict: 'El contenido cambió. Actualiza la página e inténtalo nuevamente.',
  network_error: 'No pudimos comunicarnos con el servicio. Revisa tu conexión e inténtalo nuevamente.',
  unexpected_response: 'Recibimos una respuesta inesperada. Inténtalo nuevamente y, si continúa, contacta con soporte.',
  internal_error: 'No pudimos completar la operación por un problema interno. Inténtalo nuevamente y, si continúa, contacta con soporte.',
  request_error: 'No pudimos completar la solicitud. Revisa los datos e inténtalo nuevamente.',
};

const STATUS_CODES = {
  400: 'validation_error',
  401: 'authentication_required',
  403: 'permission_denied',
  404: 'not_found',
  409: 'conflict',
  500: 'internal_error',
};

export class AppError extends Error {
  constructor({ status = 0, code, userMessage, fieldErrors = {}, requestId = null, technical = {} }) {
    super(userMessage);
    this.name = 'AppError';
    this.status = status;
    this.code = code;
    this.userMessage = userMessage;
    this.fieldErrors = fieldErrors;
    this.requestId = requestId;
    this.technical = technical;
  }
}

function legacyFields(payload) {
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) return {};
  return Object.fromEntries(
    Object.entries(payload).filter(([key, value]) => (
      !['detail', 'error', 'message', 'code', 'request_id'].includes(key)
      && (Array.isArray(value) || (value && typeof value === 'object'))
    )),
  );
}

export function normalizeApiError({ status = 0, payload = null, requestId = null, technical = {} }) {
  const publicError = payload?.error && typeof payload.error === 'object'
    ? payload.error
    : null;
  const code = publicError?.code || STATUS_CODES[status] || 'request_error';
  const fieldErrors = publicError?.fields || legacyFields(payload);
  const safeMessage = publicError?.message || USER_MESSAGES[code] || USER_MESSAGES.request_error;

  return new AppError({
    status,
    code,
    userMessage: safeMessage,
    fieldErrors,
    requestId: publicError?.request_id || requestId,
    technical,
  });
}

export function networkError(cause, technical = {}) {
  return new AppError({
    code: 'network_error',
    userMessage: USER_MESSAGES.network_error,
    technical: { ...technical, cause },
  });
}

export function unexpectedResponseError(status, technical = {}) {
  return new AppError({
    status,
    code: 'unexpected_response',
    userMessage: USER_MESSAGES.unexpected_response,
    technical,
  });
}

export function logTechnicalError(error, context = {}) {
  if (import.meta.env?.DEV) {
    console.error('API request failed', {
      status: error.status,
      code: error.code,
      requestId: error.requestId,
      technical: error.technical,
      context,
    });
  }
}

export function firstFieldError(error, field) {
  const value = error?.fieldErrors?.[field];
  if (Array.isArray(value)) return String(value[0] || '');
  if (typeof value === 'string') return value;
  return '';
}

export function notifyApiError(addNotification, error, title = 'No se pudo completar la operación') {
  logTechnicalError(error, { title });
  const message = error instanceof AppError
    ? error.userMessage
    : USER_MESSAGES.internal_error;
  addNotification(title, message, 'error');
}
