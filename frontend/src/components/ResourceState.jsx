import { Link } from 'react-router-dom';

const messages = {
  loading: 'Cargando contenido...',
  unavailable: 'El contenido solicitado ya no está disponible o no existe.',
  error: 'No pudimos cargar este contenido. Inténtalo nuevamente.',
};

export default function ResourceState({ type = 'loading', message, backTo, backLabel = 'Volver' }) {
  return (
    <div className="view-container" style={{ minHeight: '55vh', display: 'grid', placeItems: 'center', padding: '48px 24px' }}>
      <div style={{ maxWidth: '520px', textAlign: 'center' }}>
        <h2 className="h-3" style={{ marginBottom: '16px' }}>
          {type === 'loading' ? 'Un momento' : 'Contenido no disponible'}
        </h2>
        <p style={{ color: 'var(--ink-60)', marginBottom: backTo ? '24px' : 0 }}>{message || messages[type]}</p>
        {backTo && <Link className="btn btn--outline" to={backTo}>{backLabel}</Link>}
      </div>
    </div>
  );
}
