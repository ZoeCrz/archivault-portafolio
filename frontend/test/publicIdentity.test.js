import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const html = readFileSync(new URL('../index.html', import.meta.url), 'utf8');
const app = readFileSync(new URL('../src/App.jsx', import.meta.url), 'utf8');
const shell = readFileSync(new URL('../src/components/navigation/AppShell.jsx', import.meta.url), 'utf8');
const notFound = readFileSync(new URL('../src/pages/public/NotFound.jsx', import.meta.url), 'utf8');
const css = readFileSync(new URL('../src/index.css', import.meta.url), 'utf8');

test('metadata identifica la aplicación en español sin favicon genérico', () => {
  assert.match(html, /<html lang="es">/);
  assert.match(html, /<title>ArchiVault \| Colecciones y comunidad<\/title>/);
  assert.doesNotMatch(html, /favicon\.svg|<title>frontend<\/title>/);
});

test('AppShell ofrece un salto de teclado hacia el contenido principal', () => {
  assert.match(shell, /className="skip-link" href="#main-content"/);
  assert.match(shell, /<main id="main-content" className="app-shell__main" tabIndex="-1">/);
  assert.match(css, /\.skip-link:focus \{ transform: translateY\(0\); \}/);
});

test('la ruta pública desconocida conserva PublicLayout y no sustituye RequireAuth', () => {
  const privateMarker = app.indexOf('{/* --- RUTAS PRIVADAS --- */}');
  const publicBlock = app.slice(0, privateMarker);
  const privateBlock = app.slice(privateMarker);
  assert.match(publicBlock, /<Route path="\*" element=\{<NotFound \/>\} \/>/);
  assert.match(privateBlock, /<Route element=\{<RequireAuth \/>\}>/);
  assert.match(privateBlock, /<Route path="\/app" element=\{<PrivateLayout \/>\}>/);
});

test('404 es amigable, tiene un único h1 y permite volver al inicio', () => {
  assert.equal((notFound.match(/<h1\b/g) || []).length, 1);
  assert.match(notFound, /Página no encontrada/);
  assert.match(notFound, /to="\/"/);
  assert.doesNotMatch(notFound, /window\.location|navigate\(|apiRequest/);
});
