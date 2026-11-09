import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const css = readFileSync(new URL('../src/index.css', import.meta.url), 'utf8');

test('la base responsive expone tokens y contenedores opt-in', () => {
  for (const token of [
    '--content-wide',
    '--content-standard',
    '--content-readable',
    '--content-narrow',
    '--layout-gutter',
    '--layout-section-space',
    '--layout-gap',
    '--touch-target',
  ]) assert.match(css, new RegExp(`${token}:`));

  for (const className of [
    'layout-container',
    'layout-container--wide',
    'layout-container--readable',
    'layout-container--narrow',
    'layout-stack',
    'layout-cluster',
    'layout-toolbar',
    'layout-sidebar',
    'layout-grid',
    'touch-target',
    'responsive-media',
    'text-wrap-safe',
    'scroll-x',
  ]) assert.match(css, new RegExp(`\\.${className}(?:[\\s,{])`));
});

test('sidebar y toolbar tienen adaptaciones declarativas', () => {
  assert.match(css, /@media \(max-width: 1024px\)[\s\S]*?\.layout-sidebar/);
  assert.match(css, /@media \(max-width: 480px\)[\s\S]*?\.layout-toolbar--stack-mobile/);
});

test('la base responsive ya no depende de selectores de layout basados en style', () => {
  assert.doesNotMatch(css, /div\[style\*=/);
  assert.doesNotMatch(css, /\.product-grid/);
  assert.doesNotMatch(css, /\.marketplace-layout/);
  assert.match(css, /\[style\*="--serif"\]/);
});

test('los botones iconográficos de piezas no heredan ancho completo en móvil', () => {
  assert.match(css, /@media \(max-width: 480px\)[\s\S]*?\.collection-piece-card__actions \.btn \{ width: auto; margin-bottom: 0; \}/);
});
