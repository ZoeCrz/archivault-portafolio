import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const css = readFileSync(new URL('../src/index.css', import.meta.url), 'utf8');
const profile = readFileSync(new URL('../src/pages/private/Perfil.jsx', import.meta.url), 'utf8');
const publicProfile = readFileSync(new URL('../src/pages/private/PerfilPublico.jsx', import.meta.url), 'utf8');
const landing = readFileSync(new URL('../src/pages/public/Landing.jsx', import.meta.url), 'utf8');
const login = readFileSync(new URL('../src/pages/public/Login.jsx', import.meta.url), 'utf8');
const signup = readFileSync(new URL('../src/pages/public/CrearCuenta.jsx', import.meta.url), 'utf8');
const information = readFileSync(new URL('../src/components/public/InformationPage.jsx', import.meta.url), 'utf8');

test('perfil propio y público conservan sus contratos con layout adaptable', () => {
  assert.match(profile, /profile-page__identity-copy/);
  assert.match(profile, /onChange=\{event => setAvatarFile/);
  assert.match(profile, /onClick=\{save\}/);
  assert.match(profile, /checked=\{draft\.perfil_publico\}/);
  assert.match(publicProfile, /profile-page--public/);
  assert.match(publicProfile, /profile-public-list/);
  assert.match(css, /\.profile-page__identity h1[\s\S]*?font-size: clamp/);
});

test('landing usa una estructura responsive sin alterar sus destinos', () => {
  assert.match(landing, /split-hero landing-hero/);
  assert.match(landing, /landing-benefits/);
  assert.match(landing, /to="\/crear-cuenta"/);
  assert.match(landing, /href="#beneficios"/);
  assert.match(css, /@media \(max-width: 480px\)[\s\S]*?\.landing-benefits/);
});

test('autenticación conserva submits, deep link y endpoints con cards adaptables', () => {
  assert.match(login, /className="view-container auth-page"/);
  assert.match(login, /onSubmit=\{handleLogin\}/);
  assert.match(login, /safePrivateReturnPath\(location\.state\?\.from\)/);
  assert.match(login, /\/api\/v1\/accounts\/login\//);
  assert.match(signup, /className="view-container auth-page"/);
  assert.match(signup, /onSubmit=\{handleRegistro\}/);
  assert.match(signup, /\/api\/v1\/accounts\/users\//);
});

test('las páginas informativas conservan contenido estructurado y lectura responsive', () => {
  assert.match(information, /<article className="information-page">/);
  assert.match(information, /role="note"/);
  assert.match(information, /information-page__index/);
  assert.match(css, /\.information-page__header h1[\s\S]*?font-size: clamp/);
  assert.match(css, /@media \(max-width: 768px\)[\s\S]*?\.information-page__index ul/);
});
