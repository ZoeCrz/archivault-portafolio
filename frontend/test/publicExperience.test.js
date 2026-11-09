import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const landing = readFileSync(new URL('../src/pages/public/Landing.jsx', import.meta.url), 'utf8');
const login = readFileSync(new URL('../src/pages/public/Login.jsx', import.meta.url), 'utf8');
const signup = readFileSync(new URL('../src/pages/public/CrearCuenta.jsx', import.meta.url), 'utf8');
const css = readFileSync(new URL('../src/index.css', import.meta.url), 'utf8');

test('landing comunica capacidades existentes y dirige el CTA al registro', () => {
  assert.match(landing, /to="\/crear-cuenta"/);
  assert.match(landing, /colecciones e inventario/);
  assert.match(landing, /Publicaciones y ofertas/);
  assert.equal((landing.match(/<h1\b/g) || []).length, 1);
  assert.match(landing, /<h2 id="beneficios-title"/);
  assert.doesNotMatch(landing, /primera plataforma|Marketplace Seguro|verificados|libre de especuladores|alta resolución|control total sobre el valor|intercambia/i);
});

test('hero usa una composición decorativa estable sin assets genéricos', () => {
  assert.match(landing, /className="hero-image landing-hero__visual"/);
  assert.match(landing, /className="landing-hero__artifact" aria-hidden="true"/);
  assert.match(landing, /landing-hero__archive-card--front/);
  assert.doesNotMatch(landing, /ph ph--sea|hero\.png|react\.svg|vite\.svg|<img/);
  assert.match(landing, /to="\/crear-cuenta" className="btn btn--sea"/);
});

test('login asocia campos y conserva el retorno privado seguro', () => {
  assert.equal((login.match(/<h1\b/g) || []).length, 1);
  assert.match(login, /htmlFor="login-username"/);
  assert.match(login, /id="login-username"/);
  assert.match(login, /autoComplete="username"/);
  assert.match(login, /autoComplete="current-password"/);
  assert.match(login, /safePrivateReturnPath\(location\.state\?\.from\)/);
  assert.match(login, /registrationSuccess/);
});

test('registro previene doble envío y confirma el éxito sin cambiar su contrato', () => {
  assert.equal((signup.match(/<h1\b/g) || []).length, 1);
  assert.match(signup, /if \(loading\) return/);
  assert.match(signup, /disabled=\{loading\}/);
  assert.match(signup, /aria-busy=\{loading\}/);
  assert.match(signup, /type="email"/);
  assert.match(signup, /autoComplete="new-password"/);
  assert.match(signup, /navigate\('\/login', \{ replace: true, state: \{ registrationSuccess: true \} \}\)/);
  assert.match(signup, /JSON\.stringify\(nuevoUsuario\)/);
  assert.match(signup, /\/api\/v1\/accounts\/users\//);
});

test('la experiencia pública aplica contraste y foco locales', () => {
  assert.match(css, /\.auth-card__error[\s\S]*?background: #8f2d1c/);
  assert.match(css, /\.auth-card__alternate-link[\s\S]*?color: var\(--sea\)/);
  assert.match(css, /\.information-page a:focus-visible/);
  assert.match(css, /\.footer__col a\[aria-current="page"\]/);
  assert.doesNotMatch(landing, /color: 'var\(--ink-60\)'/);
});
