export default function AppShell({ announcement = null, header, children, footer = null }) {
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">Saltar al contenido principal</a>
      {announcement}
      {header}
      <main id="main-content" className="app-shell__main" tabIndex="-1">{children}</main>
      {footer}
    </div>
  );
}
