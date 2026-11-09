import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const css = readFileSync(new URL('../src/index.css', import.meta.url), 'utf8');
const collections = readFileSync(new URL('../src/pages/private/MisColecciones.jsx', import.meta.url), 'utf8');
const detail = readFileSync(new URL('../src/pages/private/DetalleColeccion.jsx', import.meta.url), 'utf8');
const newPiece = readFileSync(new URL('../src/pages/private/NuevaPieza.jsx', import.meta.url), 'utf8');

test('las vistas de colecciones adoptan contenedores, grids y toolbars responsive', () => {
  assert.match(collections, /layout-container--wide collections-page/);
  assert.match(collections, /layout-grid collections-grid/);
  assert.match(collections, /collections-list/);
  assert.match(collections, /className="collection-card__link" to=\{resourceRoutes\.collection\(col\.id\)\}/);
  assert.match(detail, /layout-container--wide collection-detail-page/);
  assert.match(detail, /layout-grid collection-pieces-grid/);
  assert.match(css, /@media \(max-width: 480px\)[\s\S]*?\.collection-card--list/);
});

test('Nueva Pieza adapta formulario, campos y multimedia sin cambiar el submit', () => {
  assert.match(newPiece, /className="new-piece-form" onSubmit=\{handleSubmit\}/);
  assert.match(newPiece, /new-piece-form__new-collection/);
  assert.match(newPiece, /new-piece-form__fields--split/);
  assert.match(newPiece, /new-piece-form__preview/);
  assert.match(newPiece, /onChange=\{handleImageUpload\}/);
  assert.match(newPiece, /onChange=\{handleColImageUpload\}/);
  assert.match(newPiece, /onClick=\{\(\) => navigate\('\/app\/colecciones'\)\}/);
});

test('las acciones funcionales de colecciones y piezas conservan sus handlers', () => {
  assert.match(collections, /onClick=\{handleSaveCollection\}/);
  assert.match(collections, /onClick=\{handleDeleteConfirm\}/);
  assert.match(collections, /onSubmit=\{handleSellCollection\}/);
  assert.match(detail, /onClick=\{handleEditarPieza\}/);
  assert.match(detail, /onClick=\{handleDeletePiezaConfirm\}/);
  assert.match(detail, /onSubmit=\{handleVenderPieza\}/);
});
