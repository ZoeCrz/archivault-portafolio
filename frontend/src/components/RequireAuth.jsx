import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { getRequestedPath } from '../services/routes';

export default function RequireAuth() {
  const location = useLocation();
  const userId = Number.parseInt(localStorage.getItem('archivault_user_id'), 10);
  const hasSession = Boolean(localStorage.getItem('archivault_refresh_token')) && Number.isInteger(userId);

  if (!hasSession) {
    return <Navigate to="/login" replace state={{ from: getRequestedPath(location) }} />;
  }

  return <Outlet />;
}
