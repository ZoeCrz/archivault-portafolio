import { Link } from 'react-router-dom';

export default function SiteBrand({ to }) {
  return (
    <Link to={to} className="topbar__brand" aria-label="ArchiVault">
      ArchiVault <sup>EST. 2026</sup>
    </Link>
  );
}
