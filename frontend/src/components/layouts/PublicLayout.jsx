import { Outlet } from 'react-router-dom';
import AppShell from '../navigation/AppShell.jsx';
import PublicHeaderActions from '../navigation/PublicHeaderActions.jsx';
import SiteFooter from '../navigation/SiteFooter.jsx';
import SiteHeader from '../navigation/SiteHeader.jsx';
import {
  AUTHENTICATED_PUBLIC_FOOTER_GROUPS,
  PUBLIC_BRAND_PATH,
  PUBLIC_FOOTER_GROUPS,
  PUBLIC_NAVIGATION,
} from '../navigation/navigationConfig.js';

function PublicAnnouncement() {
  return (
    <div className="marquee" aria-label="Acerca de ArchiVault">
      <span><span className="dot"></span> ARCHIVAULT EST. 2026</span>
      <span><span className="dot"></span> PLATAFORMA PARA COLECCIONISTAS</span>
      <span><span className="dot"></span> GESTIÓN, MARKETPLACE Y COMUNIDAD</span>
      <span><span className="dot"></span> PROTEGE TU LEGADO</span>
      <span><span className="dot"></span> ARCHIVAULT EST. 2026</span>
    </div>
  );
}

export default function PublicLayout() {
  const userId = Number.parseInt(localStorage.getItem('archivault_user_id'), 10);
  const hasStoredSession = Boolean(localStorage.getItem('archivault_refresh_token')) && Number.isInteger(userId);

  return (
    <AppShell
      announcement={<PublicAnnouncement />}
      header={(
        <SiteHeader
          brandTo={PUBLIC_BRAND_PATH}
          navigationItems={PUBLIC_NAVIGATION}
          actions={<PublicHeaderActions isAuthenticated={hasStoredSession} />}
        />
      )}
      footer={<SiteFooter brandTo={PUBLIC_BRAND_PATH} groups={hasStoredSession ? AUTHENTICATED_PUBLIC_FOOTER_GROUPS : PUBLIC_FOOTER_GROUPS} />}
    >
      <Outlet />
    </AppShell>
  );
}
