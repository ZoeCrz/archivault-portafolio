import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <section className="public-not-found" aria-labelledby="not-found-title">
      <div className="eyebrow">ERROR 404</div>
      <h1 id="not-found-title" className="h-1">Página no encontrada</h1>
      <p>La dirección que intentaste abrir no existe o ya no está disponible.</p>
      <Link className="btn btn--ink" to="/">Volver al inicio</Link>
    </section>
  );
}
