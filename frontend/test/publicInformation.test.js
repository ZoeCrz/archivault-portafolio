import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

import {
  PROVISIONAL_LEGAL_NOTICE,
  PUBLIC_INFORMATION_PAGES,
  PUBLIC_INFORMATION_PATHS,
  contactContent,
  privacyContent,
  termsContent,
} from '../src/content/publicInformation.js';
import {
  PRIVATE_FOOTER_GROUPS,
  PUBLIC_FOOTER_GROUPS,
} from '../src/components/navigation/navigationConfig.js';

const informationPaths = Object.values(PUBLIC_INFORMATION_PATHS);

function flattenText(value) {
  return JSON.stringify(value);
}

test('declara las cuatro páginas públicas requeridas', () => {
  assert.deepEqual(informationPaths, ['/ayuda', '/privacidad', '/terminos', '/contacto']);
  assert.deepEqual(PUBLIC_INFORMATION_PAGES.map(page => page.path), informationPaths);
});

test('las cuatro rutas están bajo PublicLayout y fuera de RequireAuth', () => {
  const appSource = readFileSync(new URL('../src/App.jsx', import.meta.url), 'utf8');
  const publicBlockEnd = appSource.indexOf('{/* --- RUTAS PRIVADAS --- */}');
  const publicBlock = appSource.slice(0, publicBlockEnd);
  const privateBlock = appSource.slice(publicBlockEnd);
  for (const path of informationPaths) {
    assert.match(publicBlock, new RegExp(`path="${path}"`));
    assert.doesNotMatch(privateBlock, new RegExp(`path="${path}"`));
  }
});

test('ambos footers contienen los cuatro destinos informativos reales', () => {
  for (const groups of [PUBLIC_FOOTER_GROUPS, PRIVATE_FOOTER_GROUPS]) {
    const links = groups.flatMap(group => group.links.map(link => link.to));
    for (const path of informationPaths) assert.ok(links.includes(path));
  }
});

test('privacidad y términos muestran el aviso provisional completo', () => {
  assert.equal(privacyContent.notice, PROVISIONAL_LEGAL_NOTICE);
  assert.equal(termsContent.notice, PROVISIONAL_LEGAL_NOTICE);
  assert.match(flattenText(privacyContent), /pendiente antes de producción/i);
  assert.match(flattenText(termsContent), /pendientes antes de producción/i);
});

test('contacto no simula un canal operativo ni contiene datos inventados', () => {
  const text = flattenText(contactContent);
  assert.match(text, /no dispone de un canal operativo/i);
  assert.doesNotMatch(text, /<form|mailto:|https?:\/\//i);
  assert.doesNotMatch(text, /[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}/);
  assert.doesNotMatch(text, /\+?\d[\d\s().-]{7,}\d/);
  assert.doesNotMatch(text, /razón social|domicilio de ArchiVault/i);
});

test('la plantilla contiene un solo h1 y encabezados jerárquicos', () => {
  const template = readFileSync(
    new URL('../src/components/public/InformationPage.jsx', import.meta.url),
    'utf8',
  );
  assert.equal((template.match(/<h1\b/g) || []).length, 1);
  assert.match(template, /<h2>/);
  assert.match(template, /<h3>/);
  assert.match(template, /role="note"/);
});

test('cada sección tiene un identificador estable y único por página', () => {
  for (const page of PUBLIC_INFORMATION_PAGES) {
    const ids = page.sections.map(section => section.id);
    assert.equal(new Set(ids).size, ids.length);
    assert.ok(ids.every(id => /^[a-z0-9-]+$/.test(id)));
  }
});
