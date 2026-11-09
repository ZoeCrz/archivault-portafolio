import { Link } from 'react-router-dom';
import { Icons } from '../Icons.jsx';

export default function PrivateHeaderActions({
  searchValue,
  onSearchChange,
  onSearchKeyDown,
  notificationsOpen,
  onNotificationsToggle,
  unreadCount,
  notificationPanel,
  onLogout,
}) {
  return (
    <>
      <div className="topbar__search topbar__search--interactive">
        <span aria-hidden="true"><Icons.Search /></span>
        <input
          type="search"
          aria-label="Buscar en el marketplace"
          placeholder="BUSCAR (ENTER PARA MERCADO)"
          value={searchValue}
          onChange={onSearchChange}
          onKeyDown={onSearchKeyDown}
        />
      </div>

      <div className="topbar__notification-anchor">
        <button
          type="button"
          className="topbar__icon"
          onClick={onNotificationsToggle}
          aria-label={unreadCount > 0 ? `Notificaciones, ${unreadCount} sin leer` : 'Notificaciones'}
          aria-expanded={notificationsOpen}
          style={{ background: notificationsOpen ? 'var(--paper-2)' : 'transparent' }}
        >
          <Icons.Bell />
          {unreadCount > 0 && <span className="topbar__notification-dot" aria-hidden="true"></span>}
        </button>
        {notificationPanel}
      </div>

      <Link to="/app/perfil" className="topbar__icon" aria-label="Mi perfil">
        <Icons.User />
      </Link>
      <button type="button" className="btn btn--outline btn--sm" onClick={onLogout}>Salir</button>
    </>
  );
}
