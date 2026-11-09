import { useState } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { apiRequest, clearSession } from '../../services/api';
import { AppError, unexpectedResponseError } from '../../services/errors';
import { safePrivateReturnPath } from '../../services/routes';

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [loading, setLoading] = useState(false);
  const registrationSuccess = location.state?.registrationSuccess === true;

  const handleLogin = async (e) => {
    e.preventDefault();
    setErrorMsg(''); 
    setLoading(true);

    const API_URL = import.meta.env.VITE_API_URL || window.location.origin;

    try {
        const data = await apiRequest(`${API_URL}/api/v1/accounts/login/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        }, { authenticated: false });

        clearSession();
        const idToSave = data?.user_id || data?.id;
        if (!idToSave || !data?.access || !data?.refresh) {
            throw unexpectedResponseError(200, { operation: 'login' });
        }

        localStorage.setItem('archivault_user', username);
        localStorage.setItem('archivault_user_id', idToSave.toString());
        localStorage.setItem('archivault_access_token', data.access);
        localStorage.setItem('archivault_refresh_token', data.refresh);
        navigate(safePrivateReturnPath(location.state?.from), { replace: true });
    } catch (error) {
        setErrorMsg(error instanceof AppError ? error.userMessage : 'No pudimos iniciar sesión. Inténtalo nuevamente.');
    } finally {
        setLoading(false);
    }
  };

  return (
    <div className="view-container auth-page">
      <div className="auth-card">
        <h1 className="h-2" style={{marginBottom: '32px'}}>Iniciar Sesión</h1>

        {registrationSuccess && (
            <div className="auth-card__success" role="status">
                Tu cuenta se creó correctamente. Ya puedes iniciar sesión.
            </div>
        )}
        
        {errorMsg && (
            <div id="login-error" className="auth-card__error" role="alert">
                {errorMsg}
            </div>
        )}

        <form onSubmit={handleLogin}>
          <div className="form-group" style={{marginBottom: '24px'}}>
            <label className="eyebrow" htmlFor="login-username">NOMBRE DE USUARIO</label>
            <input 
                id="login-username"
                type="text" 
                className="editorial-input" 
                placeholder="Ej. Zoe" 
                value={username} 
                onChange={(e) => setUsername(e.target.value)} 
                autoComplete="username"
                aria-invalid={Boolean(errorMsg)}
                aria-describedby={errorMsg ? 'login-error' : undefined}
                required 
            />
          </div>
          <div className="form-group" style={{marginBottom: '40px'}}>
            <label className="eyebrow" htmlFor="login-password">CONTRASEÑA</label>
            <input 
                id="login-password"
                type="password" 
                className="editorial-input" 
                placeholder="••••••••" 
                value={password} 
                onChange={(e) => setPassword(e.target.value)} 
                autoComplete="current-password"
                aria-invalid={Boolean(errorMsg)}
                aria-describedby={errorMsg ? 'login-error' : undefined}
                required 
            />
          </div>
          <button type="submit" className="btn btn--ink auth-card__submit" disabled={loading}>
            {loading ? 'Autenticando...' : 'Entrar al Sistema'}
          </button>
        </form>
        
        <div className="auth-card__alternate">
          ¿Aún no tienes una bóveda? <br/>
          <Link to="/crear-cuenta" className="auth-card__alternate-link">
            Crear mi cuenta gratuita
          </Link>
        </div>
      </div>
    </div>
  );
}
