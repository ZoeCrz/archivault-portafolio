import { Icons } from './Icons';

export default function EmptyState({ titulo, descripcion, botonTexto, onClickBoton }) {
  return (
    <div style={{ padding: '80px 24px', textAlign: 'center', border: '1px dashed var(--ink-20)', borderRadius: '4px', background: 'var(--paper-2)', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <Icons.Inbox />
      <h3 className="h-3" style={{ color: 'var(--ink-60)', marginTop: '24px' }}>{titulo}</h3>
      <p style={{ color: 'var(--ink-60)', marginTop: '12px', maxWidth: '400px' }}>{descripcion}</p>
      {botonTexto && (
        <button className="btn btn--primary" style={{ marginTop: '24px' }} onClick={onClickBoton}>
          {botonTexto}
        </button>
      )}
    </div>
  );
}