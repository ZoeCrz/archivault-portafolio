import { useId, useState } from 'react';
import { useLocation } from 'react-router-dom';
import PrimaryNavigation from './PrimaryNavigation.jsx';
import SiteBrand from './SiteBrand.jsx';

export default function SiteHeader({ brandTo, navigationItems, actions = null }) {
  const navigationId = useId();
  const { pathname } = useLocation();
  const [menuState, setMenuState] = useState({ open: false, pathname });
  const menuOpen = menuState.open && menuState.pathname === pathname;
  const closeMenu = () => setMenuState({ open: false, pathname });

  return (
    <header
      className="topbar"
      data-menu-open={menuOpen ? 'true' : 'false'}
      onKeyDown={event => { if (event.key === 'Escape') closeMenu(); }}
    >
      <SiteBrand to={brandTo} />
      <button
        type="button"
        className="topbar__menu-toggle touch-target"
        aria-controls={navigationId}
        aria-expanded={menuOpen}
        aria-label={menuOpen ? 'Cerrar menú de navegación' : 'Abrir menú de navegación'}
        onClick={() => setMenuState({ open: !menuOpen, pathname })}
      >
        <span aria-hidden="true">{menuOpen ? '×' : '☰'}</span>
      </button>
      <PrimaryNavigation id={navigationId} items={navigationItems} onNavigate={closeMenu} />
      <div className="topbar__right">{actions}</div>
    </header>
  );
}
