import { NavLink, useLocation } from 'react-router-dom';
import { isNavigationItemActive } from './navigationConfig.js';

export default function PrimaryNavigation({ items, ariaLabel = 'Navegación principal', id, onNavigate }) {
  const { pathname } = useLocation();

  return (
    <nav id={id} className="topbar__nav" aria-label={ariaLabel}>
      {items.map(item => {
        const active = isNavigationItemActive(item, pathname);
        return (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.exact}
            className={`nav-link${active ? ' active' : ''}`}
            aria-current={active ? 'page' : undefined}
            onClick={onNavigate}
            style={item.accent ? { color: 'var(--vermilion)', fontWeight: 700 } : undefined}
          >
            {item.label}
          </NavLink>
        );
      })}
    </nav>
  );
}
