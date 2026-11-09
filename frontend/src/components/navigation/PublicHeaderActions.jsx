import { Link, NavLink } from 'react-router-dom';

export default function PublicHeaderActions({ isAuthenticated = false }) {
  if (isAuthenticated) {
    return <Link to="/app/colecciones" className="btn btn--ink btn--sm">Volver a mi bóveda</Link>;
  }

  return (
    <>
      <NavLink to="/login" className="btn btn--outline btn--sm">Iniciar sesión</NavLink>
      <NavLink to="/crear-cuenta" className="btn btn--ink btn--sm">Crear cuenta</NavLink>
    </>
  );
}
