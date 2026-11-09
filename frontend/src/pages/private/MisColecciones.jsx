import { useState, useEffect, useCallback, useReducer, useRef } from 'react';
import { Link, useNavigate, useOutletContext } from 'react-router-dom';
import MediaImage from '../../components/MediaImage';
import FavoriteButton from '../../components/FavoriteButton';
import MarketplacePublicationForm from '../../components/MarketplacePublicationForm';
import { apiRequest } from '../../services/api';
import { notifyApiError } from '../../services/errors';
import { resourceRoutes } from '../../services/routes';
import { FAVORITE_TARGETS, indexFavorites, listFavorites } from '../../services/favorites';
import {
  createMarketplacePublication,
  createSaleFormState,
  hasSaleErrors,
  saleFieldErrorsFrom,
  saleFormReducer,
  validateSaleData,
} from '../../services/publications';

const Icons = {
  Grid: () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>,
  List: () => <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>,
  Image: () => <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>,
  Edit: () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>,
  Trash: () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 6h18"></path><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>,
  X: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>,
};

export default function MisColecciones() {
  const navigate = useNavigate();
  const { addNotification } = useOutletContext() || { addNotification: () => {} };
  
  const [colecciones, setColecciones] = useState([]);
  const [loading, setLoading] = useState(() => !Number.isNaN(
    parseInt(localStorage.getItem('archivault_user_id'), 10),
  ));
  const [viewMode, setViewMode] = useState('grid');
  const [filterType, setFilterType] = useState('todas'); 

  const modalBase = { open: false, id: null, maestraId: null, nombre: '', categoria: '', tipo: 'personal', total_piezas: '' };
  const [colModal, setColModal] = useState({ ...modalBase, isEdit: false });
  const [deleteModal, setDeleteModal] = useState({ open: false, id: null, nombre: '' });
  const [saleTarget, setSaleTarget] = useState(null);
  const [saleForm, dispatchSaleForm] = useReducer(
    saleFormReducer,
    '',
    createSaleFormState,
  );
  const [imgPreview, setImgPreview] = useState(null);
  const [imagenArchivo, setImagenArchivo] = useState(null);
  const saleRequestInFlightRef = useRef(false);

  const userId = parseInt(localStorage.getItem('archivault_user_id'), 10);
  const API_URL = import.meta.env.VITE_API_URL;

  const fetchData = useCallback(async () => {
    if (isNaN(userId)) return;
    try {
      const [dataUsu, dataMae, dataInv, dataFavorites] = await Promise.all([
          apiRequest(`${API_URL}/api/v1/catalog/colecciones-usuario/`),
          apiRequest(`${API_URL}/api/v1/catalog/colecciones/`),
          apiRequest(`${API_URL}/api/v1/catalog/inventario/`),
          listFavorites(API_URL, FAVORITE_TARGETS.COLLECTION),
      ]);
        
        const listaUsu = Array.isArray(dataUsu) ? dataUsu : (dataUsu.results || []);
        const listaMae = Array.isArray(dataMae) ? dataMae : (dataMae.results || []);
        const listaInv = Array.isArray(dataInv) ? dataInv : (dataInv.results || []);

        const maestrasInfo = {};
        listaMae.forEach(m => { maestrasInfo[m.id] = m; });
        const favoriteIndex = indexFavorites(dataFavorites).collections;

        const misColecciones = listaUsu
            .filter(c => c.user === userId)
            .map(c => {
                const maestraId = c.coleccion || c.coleccion_id;
                const maestra = maestrasInfo[maestraId] || {};
                const piezasReales = listaInv.filter(p => p.coleccion_usuario === c.id).length;
                
                return {
                    id: c.id, 
                    maestraId: maestraId,
                    nombre: maestra.nombre || `Colección #${c.id}`,
                    categoria: maestra.categoria || 'Sin Categoría',
                    tipo: maestra.tipo || 'personal',
                    propietario: maestra.propietario,
                    imagen: maestra.imagen || null,
                    total_piezas: maestra.total_piezas || 0,
                    piezas: piezasReales,
                    progreso: Number(c.progreso || 0),
                    favoriteId: favoriteIndex.get(Number(maestraId))?.id || null,
                    isFavorite: favoriteIndex.has(Number(maestraId)),
                };
            });

        const unicas = Array.from(new Map(misColecciones.map(item => [item.id, item])).values());
      setColecciones(unicas);
    } catch (error) { notifyApiError(addNotification, error, 'No se pudieron cargar tus colecciones'); } finally { setLoading(false); }
  }, [API_URL, addNotification, userId]);

  useEffect(() => {
    // Data is updated asynchronously after the requests settle.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchData();
  }, [fetchData]);

  const handleImageUpload = (e) => {
    if (e.target.files && e.target.files[0]) {
      setImagenArchivo(e.target.files[0]);
      setImgPreview(URL.createObjectURL(e.target.files[0]));
    }
  };

  const handleSaveCollection = async () => {
      if(!colModal.nombre) return;
      try {
          const formData = new FormData();
          formData.append('nombre', colModal.nombre);
          formData.append('categoria', colModal.categoria || 'General');
          formData.append('tipo', colModal.tipo);
          if (imagenArchivo) formData.append('imagen', imagenArchivo);
          if (colModal.tipo === 'personal') {
              formData.append('propietario', userId);
          }
          if (colModal.tipo === 'global' && colModal.total_piezas) {
              formData.append('total_piezas', colModal.total_piezas);
          } else {
              formData.append('total_piezas', 0);
          }

          let dataMaestra;
          if (colModal.isEdit) {
              dataMaestra = await apiRequest(`${API_URL}/api/v1/catalog/colecciones/${colModal.maestraId}/`, {
                  method: 'PATCH', body: formData
              });
          } else {
              dataMaestra = await apiRequest(`${API_URL}/api/v1/catalog/colecciones/`, {
                  method: 'POST', body: formData
              });
          }

          if (!colModal.isEdit) {
                  await apiRequest(`${API_URL}/api/v1/catalog/colecciones-usuario/`, {
                      method: 'POST', headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ coleccion: dataMaestra.id, user: userId })
                  });
                  addNotification("Bóveda Creada", `Colección "${colModal.nombre}" guardada exitosamente.`, "success");
          } else {
                  addNotification("Bóveda Actualizada", `Cambios guardados correctamente.`, "success");
          }

          setColModal({ ...modalBase, isEdit: false });
          setImgPreview(null); setImagenArchivo(null);
          fetchData();
      } catch (error) {
          notifyApiError(addNotification, error, 'No se pudo guardar la colección');
      }
  };

  const handleDeleteConfirm = async () => {
      try {
          await apiRequest(`${API_URL}/api/v1/catalog/colecciones-usuario/${deleteModal.id}/`, { method: 'DELETE' });
          addNotification("Eliminación Exitosa", `Colección retirada de tu bóveda.`, "info");
          setDeleteModal({ open: false, id: null, nombre: '' });
          fetchData();
      } catch (error) { notifyApiError(addNotification, error, 'No se pudo eliminar la colección'); }
  };

  const resetSaleModal = useCallback((type = 'cancel') => {
      setSaleTarget(null);
      dispatchSaleForm({ type, initialCondition: '' });
  }, []);

  const cancelSaleModal = useCallback(() => {
      if (!saleForm.submitting && !saleRequestInFlightRef.current) resetSaleModal();
  }, [resetSaleModal, saleForm.submitting]);

  useEffect(() => {
      if (!saleTarget) return undefined;
      const handleEscape = event => {
          if (event.key === 'Escape') cancelSaleModal();
      };
      document.addEventListener('keydown', handleEscape);
      return () => document.removeEventListener('keydown', handleEscape);
  }, [cancelSaleModal, saleTarget]);

  const handleSellCollection = async () => {
      if (!saleTarget || saleForm.submitting || saleRequestInFlightRef.current) return;
      const validationErrors = validateSaleData(saleForm.data);
      if (hasSaleErrors(validationErrors)) {
          dispatchSaleForm({ type: 'errors', errors: validationErrors });
          return;
      }
      saleRequestInFlightRef.current = true;
      dispatchSaleForm({ type: 'submit' });
      try {
          await createMarketplacePublication(API_URL, {
              targetType: 'collection',
              targetId: saleTarget.id,
              data: saleForm.data,
          });
          addNotification("Publicación Exitosa", `La colección "${saleTarget.nombre}" está en el Marketplace.`, "success");
          resetSaleModal('success');
      } catch (error) {
          const fieldErrors = saleFieldErrorsFrom(error);
          if (hasSaleErrors(fieldErrors)) {
              dispatchSaleForm({ type: 'errors', errors: fieldErrors });
          } else {
              notifyApiError(addNotification, error, 'No se pudo publicar la colección');
          }
      } finally {
          saleRequestInFlightRef.current = false;
          dispatchSaleForm({ type: 'settled' });
      }
  };

  if (loading) return <div className="collection-state">Sincronizando Bóveda...</div>;

  const coleccionesFiltradas = colecciones.filter(col => {
      if (filterType === 'todas') return true;
      if (filterType === 'favoritas') return col.isFavorite;
      return col.tipo === filterType;
  });

  const updateCollectionFavorite = (collectionId, state) => {
      setColecciones(previous => previous.map(collection => collection.id === collectionId
          ? { ...collection, isFavorite: state.isFavorite, favoriteId: state.favoriteId }
          : collection));
  };

  return (
    <div className="view-container layout-container layout-container--wide collections-page">
      
      <div className="h-section collections-page__header">
        <div>
          <div className="eyebrow">TU INVENTARIO REAL</div>
          <h1 className="h-1" style={{marginTop: '16px'}}>Mis Colecciones</h1>
        </div>
        <div className="collections-page__header-actions">
            <div className="view-switcher">
                <button className="view-switcher__button" aria-pressed={viewMode === 'grid'} onClick={() => setViewMode('grid')}><Icons.Grid /> Cuadrícula</button>
                <button className="view-switcher__button" aria-pressed={viewMode === 'list'} onClick={() => setViewMode('list')}><Icons.List /> Lista</button>
            </div>
            <button className="btn btn--sea" onClick={() => setColModal({ ...modalBase, open: true, isEdit: false })}>+ Nueva Colección</button>
        </div>
      </div>
      
      <div className="collection-filters">
          <button className={`chip ${filterType === 'todas' ? 'chip--solid' : ''}`} onClick={() => setFilterType('todas')}>Todas las Colecciones</button>
          <button className={`chip ${filterType === 'global' ? 'chip--solid' : ''}`} onClick={() => setFilterType('global')}>Oficiales (Globales)</button>
          <button className={`chip ${filterType === 'personal' ? 'chip--solid' : ''}`} onClick={() => setFilterType('personal')}>Personales</button>
          <button className={`chip ${filterType === 'favoritas' ? 'chip--solid' : ''}`} onClick={() => setFilterType('favoritas')}>Favoritas</button>
      </div>
      
      {coleccionesFiltradas.length === 0 ? (
        <div className="collection-state collection-state--empty">
          <h3 className="h-3" style={{marginBottom: '16px'}}>El espacio está vacío</h3>
          <p style={{color: 'var(--ink-60)', maxWidth: '400px', margin: '0 auto', marginBottom: '24px'}}>No hay colecciones con estos filtros. Ajusta la vista o crea una nueva.</p>
          <button className="btn btn--outline" onClick={() => setColModal({ ...modalBase, open: true, isEdit: false })}>Crear mi primera colección</button>
        </div>
      ) : (
        <div className={viewMode === 'grid' ? "layout-grid collections-grid" : "collections-list"}>
          {coleccionesFiltradas.map((col, index) => (
            <div className={`card collection-card collection-card--${viewMode}`} key={index}
                 onClick={() => navigate(resourceRoutes.collection(col.id))}>
              
              <div className={`card__media collection-card__media ph ${col.tipo === 'personal' ? 'ph--sea' : 'ph--ink'}`}>
                <MediaImage sources={col.imagen} alt={col.nombre} fallback={<Icons.Image />} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
                <div className="ph__label" style={{position: 'absolute', bottom: '8px', left: '8px'}}>{col.tipo === 'personal' ? 'PERSONAL' : 'GLOBAL'}</div>
              </div>

              <div className="card__meta collection-card__meta">
                <div className="collection-card__copy">
                  <h3 className="card__title collection-card__title"><Link className="collection-card__link" to={resourceRoutes.collection(col.id)} onClick={event => event.stopPropagation()}>{col.nombre}</Link></h3>
                  <div className="card__seller" style={{color: 'var(--sea)', fontWeight: 'bold'}}>{col.categoria}</div>
                  <div className="card__seller">{col.piezas} {col.total_piezas > 0 ? `/ ${col.total_piezas}` : ''} PIEZAS REGISTRADAS</div>
                  {col.total_piezas > 0 && (
                    <>
                      <div className="custom-progress"><div className="custom-progress-fill" style={{width: `${col.progreso}%`}}></div></div>
                      <div className="card__seller">{Math.round(col.progreso)}% COMPLETADA</div>
                    </>
                  )}
                </div>
                <div className="collection-card__actions" onClick={event => event.stopPropagation()}>
                    <FavoriteButton targetType={FAVORITE_TARGETS.COLLECTION} targetId={col.maestraId} favoriteId={col.favoriteId} isFavorite={col.isFavorite} onChange={state => updateCollectionFavorite(col.id, state)} />
                    <button className="btn btn--outline btn--sm" onClick={(e) => { e.stopPropagation(); setSaleTarget({ id: col.id, nombre: col.nombre }); dispatchSaleForm({ type: 'reset', initialCondition: '' }); }}>Vender</button>
                    <button className="btn btn--outline btn--sm" style={{padding: '8px'}} onClick={(e) => { e.stopPropagation(); setColModal({ open: true, isEdit: true, id: col.id, maestraId: col.maestraId, nombre: col.nombre, categoria: col.categoria, tipo: col.tipo, total_piezas: col.total_piezas }); setImgPreview(col.imagen); setImagenArchivo(null); }} aria-label={`Editar ${col.nombre}`} title="Editar">
                        <Icons.Edit />
                    </button>
                    <button className="btn btn--outline btn--sm" style={{padding: '8px', color: 'var(--vermilion)', borderColor: 'var(--vermilion)'}} onClick={(e) => { e.stopPropagation(); setDeleteModal({ open: true, id: col.id, nombre: col.nombre }); }} aria-label={`Eliminar ${col.nombre}`} title="Eliminar">
                        <Icons.Trash />
                    </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {colModal.open && (
          <div className="overlay-backdrop">
              <div className="overlay-panel overlay-panel--lg overlay-panel--split" role="dialog" aria-modal="true" aria-label={colModal.isEdit ? 'Editar colección' : 'Crear colección'}>
                  <button type="button" className="overlay-close" aria-label="Cerrar gestión de colección" onClick={() => {setColModal(modalBase); setImgPreview(null); setImagenArchivo(null);}}><Icons.X /></button>
                  
                  <div>
                      <div className="eyebrow" style={{marginBottom: '12px'}}>PORTADA</div>
                      {!imgPreview ? (
                          <label style={{display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '32px 16px', border: '2px dashed var(--ink-20)', borderRadius: '12px', background: 'var(--paper-2)', cursor: 'pointer', color: 'var(--ink-60)', height: '200px', textAlign: 'center'}}>
                              <Icons.Image />
                              <span style={{fontWeight: 'bold', color: 'var(--sea)', marginTop: '12px', fontSize: '14px'}}>Añadir Portada</span>
                              <input type="file" style={{display: 'none'}} accept="image/*" onChange={handleImageUpload} />
                          </label>
                      ) : (
                          <div style={{position: 'relative', borderRadius: '12px', overflow: 'hidden', border: '1px solid var(--ink-10)', height: '200px'}}>
                              <MediaImage sources={imgPreview} alt="Vista previa" fallback={<Icons.Image />} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
                              <button type="button" className="collection-media-remove" aria-label="Retirar portada" onClick={() => {setImgPreview(null); setImagenArchivo(null);}}><Icons.X /></button>
                          </div>
                      )}
                  </div>

                  <div>
                      <div className="eyebrow" style={{marginBottom: '16px', color: 'var(--sea)'}}>{colModal.isEdit ? 'ACTUALIZAR REGISTROS' : 'GESTIÓN DE BÓVEDA'}</div>
                      <h2 className="h-3" style={{marginBottom: '24px'}}>{colModal.isEdit ? 'Editar Colección' : 'Crear Colección'}</h2>
                      
                      <div className="form-group" style={{marginBottom: '20px'}}>
                          <label className="eyebrow" style={{display: 'block', marginBottom: '8px'}}>NOMBRE</label>
                          <input type="text" className="editorial-input" value={colModal.nombre} onChange={e => setColModal({...colModal, nombre: e.target.value})} placeholder="Ej. Álbum Panini Qatar 2022" autoFocus style={{fontSize: '16px', padding: '8px 0'}}/>
                      </div>

                      <div className="form-group" style={{marginBottom: '20px'}}>
                          <label className="eyebrow" style={{display: 'block', marginBottom: '8px'}}>CATEGORÍA</label>
                          <input type="text" className="editorial-input" value={colModal.categoria} onChange={e => setColModal({...colModal, categoria: e.target.value})} placeholder="Ej. Deportes, TCG, Arte..." style={{fontSize: '16px', padding: '8px 0'}} />
                      </div>

                      <div style={{display: 'grid', gridTemplateColumns: colModal.tipo === 'global' ? '1fr 1fr' : '1fr', gap: '16px', marginBottom: '32px'}}>
                        <div className="form-group" style={{marginBottom: '0'}}>
                            <label className="eyebrow" style={{display: 'block', marginBottom: '8px'}}>TIPO DE COLECCIÓN</label>
                            <select className="editorial-input" value={colModal.tipo} onChange={e => setColModal({...colModal, tipo: e.target.value})} style={{appearance: 'auto', fontSize: '14px', padding: '8px 0'}}>
                                <option value="personal">Personal (Infinita)</option>
                                <option value="global">Oficial Global (Cerrada)</option>
                            </select>
                        </div>
                        {colModal.tipo === 'global' && (
                            <div className="form-group" style={{marginBottom: '0'}}>
                                <label className="eyebrow" style={{display: 'block', marginBottom: '8px'}}>PIEZAS TOTALES</label>
                                <input type="number" className="editorial-input" value={colModal.total_piezas} onChange={e => setColModal({...colModal, total_piezas: e.target.value})} placeholder="Ej. 638" style={{fontSize: '14px', padding: '8px 0'}} />
                            </div>
                        )}
                      </div>
                      
                      <button className="btn btn--sea" style={{width: '100%', justifyContent: 'center'}} onClick={handleSaveCollection} disabled={!colModal.nombre}>
                        {colModal.isEdit ? 'Guardar Cambios' : 'Inicializar Bóveda'}
                      </button>
                  </div>
              </div>
          </div>
      )}

      {deleteModal.open && (
          <div className="overlay-backdrop">
              <div className="overlay-panel overlay-panel--sm overlay-panel--center" role="dialog" aria-modal="true" aria-label="Confirmar eliminación de colección">
                  <div style={{width: '64px', height: '64px', borderRadius: '50%', background: 'var(--negative-surface)', color: 'var(--negative)', display: 'grid', placeItems: 'center', margin: '0 auto 24px auto'}}>
                      <Icons.Trash />
                  </div>
                  <h2 className="h-3" style={{marginBottom: '16px'}}>¿Eliminar Colección?</h2>
                  <p style={{color: 'var(--ink-60)', marginBottom: '32px'}}>
                      Estás a punto de eliminar <strong>"{deleteModal.nombre}"</strong>. Esta acción quitará la colección y sus vínculos de tu bóveda.
                  </p>
                  <div className="overlay-actions overlay-actions--center">
                      <button className="btn btn--outline" onClick={() => setDeleteModal({open: false, id: null, nombre: ''})}>Cancelar</button>
                      <button className="btn btn--vermilion" onClick={handleDeleteConfirm}>Sí, Eliminar</button>
                  </div>
              </div>
          </div>
      )}

      {saleTarget && (
          <div className="overlay-backdrop">
              <div className="overlay-panel" role="dialog" aria-modal="true" aria-label="Publicar colección">
                  <button type="button" className="overlay-close" aria-label="Cerrar formulario de venta" onClick={cancelSaleModal} disabled={saleForm.submitting}><Icons.X /></button>
                  <div className="eyebrow" style={{marginBottom: '16px', color: 'var(--vermilion)'}}>PUBLICAR COLECCIÓN</div>
                  <h2 className="h-3" style={{marginBottom: '24px'}}>{saleTarget.nombre}</h2>
                  <MarketplacePublicationForm
                    value={saleForm.data}
                    onChange={(field, value) => dispatchSaleForm({ type: 'change', field, value })}
                    onSubmit={handleSellCollection}
                    onCancel={cancelSaleModal}
                    fieldErrors={saleForm.fieldErrors}
                    submitting={saleForm.submitting}
                  />
              </div>
          </div>
      )}
    </div>
  );
}
