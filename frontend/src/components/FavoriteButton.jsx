import { useRef, useState } from 'react';
import { createFavorite, deleteFavorite } from '../services/favorites';

export default function FavoriteButton({
  targetType,
  targetId,
  favoriteId = null,
  isFavorite = false,
  disabled = false,
  onChange,
}) {
  const [current, setCurrent] = useState({ isFavorite, favoriteId });
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState('');
  const inFlight = useRef(false);
  const apiUrl = import.meta.env.VITE_API_URL;

  const toggle = async event => {
    event.stopPropagation();
    if (disabled || submitting || inFlight.current) return;
    inFlight.current = true;
    setSubmitting(true);
    setMessage('');
    try {
      if (current.isFavorite) {
        await deleteFavorite(apiUrl, current.favoriteId, targetType, targetId);
        const next = { isFavorite: false, favoriteId: null, favorite: null };
        setCurrent(next);
        onChange?.(next);
      } else {
        const favorite = await createFavorite(apiUrl, targetType, targetId);
        const next = { isFavorite: true, favoriteId: favorite.id, favorite };
        setCurrent(next);
        onChange?.(next);
      }
    } catch (error) {
      setMessage(error?.userMessage || 'No pudimos actualizar este favorito. Inténtalo nuevamente.');
    } finally {
      inFlight.current = false;
      setSubmitting(false);
    }
  };

  const label = current.isFavorite ? 'Quitar de favoritos' : 'Añadir a favoritos';
  return (
    <span style={{ display: 'inline-grid', gap: '4px' }}>
      <button
        type="button"
        className="btn btn--outline btn--sm touch-target"
        aria-label={label}
        aria-pressed={current.isFavorite}
        disabled={disabled || submitting}
        onClick={toggle}
        style={{ minWidth: '44px', justifyContent: 'center' }}
      >
        <span aria-hidden="true">{current.isFavorite ? '★' : '☆'}</span>
        <span>{submitting ? 'Guardando…' : current.isFavorite ? 'En favoritos' : 'Favorito'}</span>
      </button>
      {message && <small role="status" style={{ color: 'var(--negative)', maxWidth: '220px' }}>{message}</small>}
    </span>
  );
}
