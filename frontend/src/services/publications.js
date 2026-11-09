import { apiRequest } from './api.js';

export const SALE_CONDITIONS = [
  { value: 'NUEVA', label: 'Nueva' },
  { value: 'USADA', label: 'Usada' },
  { value: 'DAÑADA', label: 'Dañada' },
];

const VALID_CONDITIONS = new Set(SALE_CONDITIONS.map(item => item.value));
const SALE_FIELDS = new Set(['precio', 'condicion', 'descripcion']);

export function createEmptySaleData(initialCondition = '') {
  return {
    precio: '',
    condicion: VALID_CONDITIONS.has(initialCondition) ? initialCondition : '',
    descripcion: '',
  };
}

export function createSaleFormState(initialCondition = '') {
  return {
    data: createEmptySaleData(initialCondition),
    fieldErrors: {},
    submitting: false,
  };
}

export function saleFormReducer(state, action) {
  switch (action.type) {
    case 'change': {
      const fieldErrors = { ...state.fieldErrors };
      delete fieldErrors[action.field];
      return {
        ...state,
        data: { ...state.data, [action.field]: action.value },
        fieldErrors,
      };
    }
    case 'errors':
      return { ...state, fieldErrors: action.errors || {}, submitting: false };
    case 'submit':
      return state.submitting ? state : { ...state, submitting: true };
    case 'settled':
      return { ...state, submitting: false };
    case 'reset':
    case 'cancel':
    case 'success':
      return createSaleFormState(action.initialCondition || '');
    default:
      return state;
  }
}

export function validateSaleData(data) {
  const errors = {};
  const rawPrice = String(data?.precio ?? '').trim();
  const numericPrice = Number(rawPrice);
  if (!rawPrice) errors.precio = ['Indica el precio de venta.'];
  else if (!Number.isFinite(numericPrice) || numericPrice <= 0) {
    errors.precio = ['El precio debe ser un número mayor que cero.'];
  }

  if (!VALID_CONDITIONS.has(data?.condicion)) {
    errors.condicion = ['Selecciona una condición válida.'];
  }

  const description = String(data?.descripcion ?? '').trim();
  if (!description) errors.descripcion = ['Añade una descripción breve.'];
  else if (description.length > 500) {
    errors.descripcion = ['La descripción no puede superar 500 caracteres.'];
  }
  return errors;
}

export function hasSaleErrors(errors) {
  return Object.keys(errors || {}).length > 0;
}

export function saleFieldErrorsFrom(error) {
  const fields = error?.fieldErrors || {};
  return Object.fromEntries(
    Object.entries(fields).filter(([field]) => SALE_FIELDS.has(field)),
  );
}

export function buildPublicationPayload({ targetType, targetId, data }) {
  const targetField = targetType === 'piece'
    ? 'pieza_inventario'
    : targetType === 'collection'
      ? 'coleccion_usuario'
      : null;
  if (!targetField) throw new TypeError('Unsupported publication target type');
  if (!VALID_CONDITIONS.has(data.condicion)) {
    throw new TypeError('Unsupported publication condition');
  }

  return {
    [targetField]: targetId,
    precio: data.precio,
    condicion: data.condicion,
    descripcion: data.descripcion.trim(),
  };
}

export async function createMarketplacePublication(apiUrl, options) {
  const payload = buildPublicationPayload(options);
  return apiRequest(`${apiUrl}/api/v1/marketplace/publicaciones/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}
