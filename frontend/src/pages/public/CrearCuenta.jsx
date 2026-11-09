import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { apiRequest } from '../../services/api';
import { AppError, firstFieldError } from '../../services/errors';

export default function CrearCuenta() {
  const navigate = useNavigate();

  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [loading, setLoading] = useState(false);

  const handleRegistro = async (e) => {
    e.preventDefault();
    if (loading) return;
    setErrorMsg(''); 

    // 1. EL GUARDIA DEL CORREO (Validación estricta de formato)
    const regexCorreo = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$/;
    if (!regexCorreo.test(email)) {
        setErrorMsg("Por favor, ingresa un formato de correo válido (ejemplo@dominio.com).");
        return; // Detenemos la ejecución aquí, no molesta a Django
    }

    // 2. VALIDACIÓN DE CONTRASEÑA MÍNIMA
    if (password.length < 8) {
        setErrorMsg("La contraseña debe tener al menos 8 caracteres.");
        return;
    }

    const nuevoUsuario = { username, email, password };
    const API_URL = import.meta.env.VITE_API_URL;

    setLoading(true);
    try {
        await apiRequest(`${API_URL}/api/v1/accounts/users/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(nuevoUsuario)
        }, { authenticated: false });
        navigate('/login', { replace: true, state: { registrationSuccess: true } });
    } catch (error) {
        if (error instanceof AppError) {
            setErrorMsg(
                firstFieldError(error, 'username')
                || firstFieldError(error, 'email')
                || firstFieldError(error, 'password')
                || error.userMessage
            );
        } else {
            setErrorMsg('No pudimos crear la cuenta. Inténtalo nuevamente.');
        }
    } finally {
        setLoading(false);
    }
  };

  return (
    <div className="view-container auth-page">
      <div className="auth-card">
        <div className="eyebrow" style={{marginBottom: '8px'}}>ÚNETE A ARCHIVAULT</div>
        <h1 className="h-2" style={{marginBottom: '32px'}}>Comienza tu legado</h1>

        {errorMsg && (
            <div id="signup-error" className="auth-card__error" role="alert">
                {errorMsg}
            </div>
        )}
        
        <form onSubmit={handleRegistro}>
          <div className="form-group">
            <label className="eyebrow" htmlFor="signup-username">NOMBRE DE USUARIO</label>
            <input id="signup-username" type="text" className="editorial-input" placeholder="Ej. Alex" value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" aria-invalid={Boolean(errorMsg)} aria-describedby={errorMsg ? 'signup-error' : undefined} required />
          </div>
          <div className="form-group">
            <label className="eyebrow" htmlFor="signup-email">CORREO ELECTRÓNICO</label>
            <input id="signup-email" type="email" className="editorial-input" placeholder="tu@correo.com" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" aria-invalid={Boolean(errorMsg)} aria-describedby={errorMsg ? 'signup-error' : undefined} required />
          </div>
          <div className="form-group" style={{marginBottom: '40px'}}>
            <label className="eyebrow" htmlFor="signup-password">CONTRASEÑA</label>
            <input id="signup-password" type="password" className="editorial-input" placeholder="Mínimo 8 caracteres" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="new-password" aria-invalid={Boolean(errorMsg)} aria-describedby={errorMsg ? 'signup-error' : undefined} required />
          </div>
          
          <button type="submit" className="btn btn--sea auth-card__submit" disabled={loading} aria-busy={loading}>
            {loading ? 'Creando tu cuenta...' : 'Crear mi bóveda'}
          </button>
        </form>

        <div className="auth-card__alternate">
          ¿Ya tienes una cuenta? <br/>
          <Link to="/login" className="auth-card__alternate-link">Iniciar sesión</Link>
        </div>
      </div>
    </div>
  );
}
