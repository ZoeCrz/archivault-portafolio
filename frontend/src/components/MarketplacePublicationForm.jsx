import { useId, useState } from 'react';
import { SALE_CONDITIONS, validateSaleData } from '../services/publications';

function firstError(value) {
  if (Array.isArray(value)) return String(value[0] || '');
  return typeof value === 'string' ? value : '';
}

export default function MarketplacePublicationForm({
  value,
  onChange,
  onSubmit,
  onCancel,
  fieldErrors = {},
  submitting = false,
  showActions = true,
  submitLabel = 'Publicar',
}) {
  const id = useId();
  const [touched, setTouched] = useState({});
  const localErrors = validateSaleData(value);
  const visibleError = field => firstError(fieldErrors[field]) || (touched[field] ? firstError(localErrors[field]) : '');
  const update = (field, nextValue) => onChange(field, nextValue);
  const blur = field => setTouched(previous => ({ ...previous, [field]: true }));

  return (
    <fieldset className="marketplace-publication-form" disabled={submitting}>
      <div className="form-group" style={{ marginBottom: '24px' }}>
        <label htmlFor={`${id}-price`} className="eyebrow" style={{ display: 'block', marginBottom: '12px' }}>PRECIO (MXN)</label>
        <input id={`${id}-price`} type="number" min="0.01" step="0.01" className="editorial-input" value={value.precio} onChange={event => update('precio', event.target.value)} onBlur={() => blur('precio')} aria-invalid={Boolean(visibleError('precio'))} required style={{ fontSize: '24px' }} />
        {visibleError('precio') && <div role="alert" style={{ color: 'var(--vermilion)', fontSize: '13px', marginTop: '8px' }}>{visibleError('precio')}</div>}
      </div>

      <div className="form-group" style={{ marginBottom: '24px' }}>
        <label htmlFor={`${id}-condition`} className="eyebrow" style={{ display: 'block', marginBottom: '12px' }}>CONDICIÓN</label>
        <select id={`${id}-condition`} className="editorial-input" value={value.condicion} onChange={event => update('condicion', event.target.value)} onBlur={() => blur('condicion')} aria-invalid={Boolean(visibleError('condicion'))} required style={{ appearance: 'auto' }}>
          <option value="" disabled>Selecciona una condición</option>
          {SALE_CONDITIONS.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}
        </select>
        {visibleError('condicion') && <div role="alert" style={{ color: 'var(--vermilion)', fontSize: '13px', marginTop: '8px' }}>{visibleError('condicion')}</div>}
      </div>

      <div className="form-group" style={{ marginBottom: showActions ? '24px' : 0 }}>
        <div className="marketplace-publication-form__label-row">
          <label htmlFor={`${id}-description`} className="eyebrow">DESCRIPCIÓN</label>
          <span style={{ color: value.descripcion.length > 500 ? 'var(--vermilion)' : 'var(--ink-60)', fontSize: '12px' }}>{value.descripcion.length}/500</span>
        </div>
        <textarea id={`${id}-description`} className="editorial-input" maxLength={500} value={value.descripcion} onChange={event => update('descripcion', event.target.value)} onBlur={() => blur('descripcion')} aria-invalid={Boolean(visibleError('descripcion'))} placeholder="Describe brevemente el estado del producto" required style={{ minHeight: '90px', resize: 'vertical' }} />
        {visibleError('descripcion') && <div role="alert" style={{ color: 'var(--vermilion)', fontSize: '13px', marginTop: '8px' }}>{visibleError('descripcion')}</div>}
      </div>

      {showActions && <div className="marketplace-publication-form__actions">
        {onCancel && <button type="button" className="btn btn--outline" onClick={onCancel} disabled={submitting}>Cancelar</button>}
        <button type="button" className="btn btn--vermilion" onClick={onSubmit} disabled={submitting}>{submitting ? 'Publicando...' : submitLabel}</button>
      </div>}
    </fieldset>
  );
}
