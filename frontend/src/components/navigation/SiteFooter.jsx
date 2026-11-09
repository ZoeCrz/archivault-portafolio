import { Link, NavLink } from 'react-router-dom';

export default function SiteFooter({ brandTo, groups }) {
  const columnClass = groups.length === 1
    ? ' footer--compact'
    : groups.length === 2
      ? ' footer--three-columns'
      : groups.length === 4 ? ' footer--five-columns' : '';
  return (
    <footer className={`footer${columnClass}`}>
      <div className="footer__col footer__identity">
        <Link to={brandTo} className="footer__brand-link">
          <div className="footer__brand">ArchiVault</div>
        </Link>
        <p className="footer__description">
          Plataforma centralizada de gestión y comunidad para coleccionistas.
        </p>
        <div className="eyebrow footer__copyright">© 2026 ArchiVault</div>
      </div>
      {groups.map(group => (
        <div className="footer__col" key={group.title}>
          <h5>{group.title}</h5>
          <ul>
            {group.links.map(link => <li key={link.to}><NavLink to={link.to} end>{link.label}</NavLink></li>)}
          </ul>
        </div>
      ))}
    </footer>
  );
}
