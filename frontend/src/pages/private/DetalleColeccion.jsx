import { useState, useEffect, useCallback, useReducer, useRef } from 'react';
import { useNavigate, useOutletContext, useParams } from 'react-router-dom';
import MediaImage from '../../components/MediaImage';
import FavoriteButton from '../../components/FavoriteButton';
import MarketplacePublicationForm from '../../components/MarketplacePublicationForm';
import ResourceState from '../../components/ResourceState';
import { apiRequest } from '../../services/api';
import { AppError, notifyApiError } from '../../services/errors';
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
  X: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>,
  Edit: () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>,
  Trash: () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 6h18"></path><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>,
  Image: () => <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
};

export default function DetalleColeccion() {
  const navigate = useNavigate();
  const { coleccionUsuarioId } = useParams();
  const { addNotification } = useOutletContext();
  const colUsuId = Number.parseInt(coleccionUsuarioId, 10);

  const [adquiridas, setAdquiridas] = useState([]);
  const [faltantes, setFaltantes] = useState([]);
  const [progreso, setProgreso] = useState(0);
  const [filtro, setFiltro] = useState('todas');
  const [loading, setLoading] = useState(true);
  const [resourceError, setResourceError] = useState(null);
  const [collectionInfo, setCollectionInfo] = useState(null);
  
  const [saleTarget, setSaleTarget] = useState(null);
  const [saleForm, dispatchSaleForm] = useReducer(
    saleFormReducer,
    'NUEVA',
    createSaleFormState,
  );
  const [editPiezaModal, setEditPiezaModal] = useState({ open: false, pieza: null, nombre: '', condicion: '' });
  const [deletePiezaModal, setDeletePiezaModal] = useState({ open: false, id: null, nombre: '' });
  const [imgPreview, setImgPreview] = useState(null);
  const [imagenArchivo, setImagenArchivo] = useState(null);
  const saleRequestInFlightRef = useRef(false);

  const API_URL = import.meta.env.VITE_API_URL;

  const fetchDetallesReales = useCallback(async () => {
    try {
      setResourceError(null);
      const dataColeccion = await apiRequest(`${API_URL}/api/v1/catalog/colecciones-usuario/${colUsuId}/`);
      const colMaeId = dataColeccion.coleccion || dataColeccion.coleccion_id;
      const [dataInv, dataCat, dataFotos, dataMaestra, dataFavorites] = await Promise.all([
          apiRequest(`${API_URL}/api/v1/catalog/inventario/`),
          apiRequest(`${API_URL}/api/v1/catalog/piezas-catalogo/`),
          apiRequest(`${API_URL}/api/v1/catalog/fotos/`),
          apiRequest(`${API_URL}/api/v1/catalog/colecciones/${colMaeId}/`),
          listFavorites(API_URL, FAVORITE_TARGETS.PIECE),
      ]);
          const tipo = dataMaestra.tipo || 'personal';
          const totalPiezas = Number(dataMaestra.total_piezas || 0);
          setCollectionInfo({
            nombre: dataMaestra.nombre || `Colección #${colUsuId}`,
            categoria: dataMaestra.categoria || 'Sin categoría',
            tipo,
            totalPiezas,
          });
          
          const listaInv = Array.isArray(dataInv) ? dataInv : (dataInv.results || []);
          const listaCat = Array.isArray(dataCat) ? dataCat : (dataCat.results || []);
          const listaFotos = Array.isArray(dataFotos) ? dataFotos : (dataFotos.results || []);
          const favoriteIndex = indexFavorites(dataFavorites).pieces;

          const misPiezasRaw = listaInv.filter(p => p.coleccion_usuario === colUsuId);
          const catalogo = listaCat.filter(c => c.coleccion === colMaeId);
          
          const misPiezas = misPiezasRaw.map(miPieza => {
              const catInfo = catalogo.find(c => c.id === miPieza.pieza_catalogo) || {};
              const foto = listaFotos.find(item => item.pieza_inventario === miPieza.id);
              return { ...miPieza, nombreRealMostrar: miPieza.nombre_personalizado || catInfo.nombre || 'Pieza Personalizada', imagenes: [foto?.archivo, foto?.url], fotoId: foto?.id || null, favoriteId: favoriteIndex.get(Number(miPieza.id))?.id || null, isFavorite: favoriteIndex.has(Number(miPieza.id)) };
          });

          let faltan = [];
          if (tipo === 'global' && totalPiezas > 0) {
              const numAdquiridas = misPiezas.length;
              if (numAdquiridas < totalPiezas) {
                  faltan = Array.from({ length: totalPiezas - numAdquiridas }, (_, i) => ({
                      numero_ficticio: numAdquiridas + i + 1,
                      nombre: "Pieza Desconocida"
                  }));
              }
          }

          setAdquiridas(misPiezas);
          setFaltantes(faltan);
          setProgreso(Number(dataColeccion.progreso || 0));
    } catch (error) {
      if (error instanceof AppError && ['not_found', 'permission_denied'].includes(error.code)) {
        setResourceError('unavailable');
      } else {
        setResourceError('error');
      }
    } finally { setLoading(false); }
  }, [API_URL, colUsuId]);

  useEffect(() => {
    if (!Number.isInteger(colUsuId)) return;
    // Data is updated asynchronously after the requests settle.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchDetallesReales();
  }, [colUsuId, fetchDetallesReales]);

  const resetSaleModal = useCallback((type = 'cancel') => {
      setSaleTarget(null);
      dispatchSaleForm({ type, initialCondition: 'NUEVA' });
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

  const handleVenderPieza = async () => {
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
              targetType: 'piece',
              targetId: saleTarget.id,
              data: saleForm.data,
          });
          addNotification("Publicación Exitosa", `Tu pieza ya está en el Marketplace.`, "success");
          resetSaleModal('success');
      } catch (error) {
          const fieldErrors = saleFieldErrorsFrom(error);
          if (hasSaleErrors(fieldErrors)) {
              dispatchSaleForm({ type: 'errors', errors: fieldErrors });
          } else {
              notifyApiError(addNotification, error, 'No se pudo publicar la pieza');
          }
      } finally {
          saleRequestInFlightRef.current = false;
          dispatchSaleForm({ type: 'settled' });
      }
  };

  const handleImageUpload = (e) => {
    if(e.target.files && e.target.files[0]) {
        setImagenArchivo(e.target.files[0]);
        setImgPreview(URL.createObjectURL(e.target.files[0]));
    }
  };

  const handleEditarPieza = async () => {
      try {
          const formData = new FormData();
          formData.append('nombre_personalizado', editPiezaModal.nombre);
          formData.append('condicion', editPiezaModal.condicion);

          await apiRequest(`${API_URL}/api/v1/catalog/inventario/${editPiezaModal.pieza.id}/`, { method: 'PATCH', body: formData });
              if (imagenArchivo) {
                  const fotoForm = new FormData();
                  fotoForm.append('pieza_inventario', editPiezaModal.pieza.id);
                  fotoForm.append('archivo', imagenArchivo);
                  const fotoUrl = editPiezaModal.pieza.fotoId
                      ? `${API_URL}/api/v1/catalog/fotos/${editPiezaModal.pieza.fotoId}/`
                      : `${API_URL}/api/v1/catalog/fotos/`;
                  await apiRequest(fotoUrl, {
                      method: editPiezaModal.pieza.fotoId ? 'PATCH' : 'POST',
                      body: fotoForm,
                  });
              }
              addNotification("Pieza Actualizada", "Inventario sincronizado.", "success");
              setEditPiezaModal({ open: false, pieza: null, nombre: '', condicion: '' });
              setImgPreview(null); setImagenArchivo(null);
              fetchDetallesReales();
      } catch (error) { notifyApiError(addNotification, error, 'No se pudo actualizar la pieza'); }
  };

  const handleDeletePiezaConfirm = async () => {
      try {
          await apiRequest(`${API_URL}/api/v1/catalog/inventario/${deletePiezaModal.id}/`, { method: 'DELETE' });
          addNotification("Pieza Eliminada", "Eliminada de tu inventario.", "info");
          setDeletePiezaModal({ open: false, id: null, nombre: '' });
          fetchDetallesReales();
      } catch (error) { notifyApiError(addNotification, error, 'No se pudo eliminar la pieza'); }
  };

  if (!Number.isInteger(colUsuId)) return <ResourceState type="unavailable" backTo="/app/colecciones" backLabel="Volver a Mis Colecciones" />;
  if (loading) return <ResourceState type="loading" />;
  if (resourceError) return <ResourceState type={resourceError} backTo="/app/colecciones" backLabel="Volver a Mis Colecciones" />;

  const { nombre: nombreColeccion, categoria, tipo, totalPiezas: total_piezas } = collectionInfo;

  let piezasARenderizar = filtro === 'todas' ? [...adquiridas.map(p => ({...p, adq: true})), ...faltantes.map(p => ({...p, adq: false}))] :
                          filtro === 'adquiridas' ? adquiridas.map(p => ({...p, adq: true})) :
                          filtro === 'favoritas' ? adquiridas.filter(p => p.isFavorite).map(p => ({ ...p, adq: true })) : faltantes.map(p => ({...p, adq: false}));

  const updatePieceFavorite = (pieceId, state) => {
      setAdquiridas(previous => previous.map(piece => piece.id === pieceId
          ? { ...piece, isFavorite: state.isFavorite, favoriteId: state.favoriteId }
          : piece));
  };

  return (
    <div className="view-container layout-container layout-container--wide collection-detail-page">
      
      <button type="button" className="eyebrow collection-detail-page__back" onClick={() => navigate('/app/colecciones')}>&larr; VOLVER AL INVENTARIO</button>
      
      <div className="h-section collection-detail-page__header">
        <div className="collection-detail-page__heading">
          <h1 className="h-1 collection-detail-page__title">{nombreColeccion || 'Colección'}</h1>
          <div className="eyebrow" style={{color: 'var(--sea)'}}>{categoria} · COLECCIÓN {tipo?.toUpperCase() || 'GENERAL'}</div>
        </div>
        <div className="collection-progress-card">
          <div className="h-2" style={{color: 'var(--vermilion)', marginBottom: '8px'}}>{total_piezas > 0 ? `${Math.round(progreso)}%` : 'SIN META'}</div>
          <div className="eyebrow">{adquiridas.length} {tipo === 'global' && total_piezas > 0 && `/ ${total_piezas}`} PIEZAS EN BÓVEDA</div>
        </div>
      </div>
      
      <div className="collection-detail-page__toolbar">
        <div className="collection-filters">
          <button className={`chip ${filtro === 'todas' ? 'chip--solid' : ''}`} onClick={() => setFiltro('todas')}>Vista Completa</button>
          <button className={`chip ${filtro === 'adquiridas' ? 'chip--solid' : ''}`} onClick={() => setFiltro('adquiridas')}>En Bóveda ({adquiridas.length})</button>
          <button className={`chip ${filtro === 'favoritas' ? 'chip--solid' : ''}`} onClick={() => setFiltro('favoritas')}>Favoritas</button>
          {tipo === 'global' && total_piezas > 0 && <button className={`chip ${filtro === 'faltantes' ? 'chip--solid' : ''}`} onClick={() => setFiltro('faltantes')}>Faltantes ({faltantes.length})</button>}
        </div>
        <button className="btn btn--sea" onClick={() => navigate('/app/nueva-pieza')}>+ Añadir Pieza a Bóveda</button>
      </div>
      
      <div className="layout-grid collection-pieces-grid">
        {piezasARenderizar.map((pieza, idx) => (
            pieza.adq ? (
                <div className="card collection-piece-card" key={`adq-${pieza.id || idx}`}>
                    <div className="card__media collection-piece-card__media ph ph--sea">
                        <MediaImage sources={pieza.imagenes} alt={pieza.nombreRealMostrar} fallback={<Icons.Image />} style={{width:'100%', height:'100%', objectFit:'cover'}} />
                    </div>
                    <div className="card__meta collection-piece-card__meta">
                        <div className="collection-piece-card__copy">
                            <div className="collection-piece-card__heading">
                                <h3 className="card__title collection-piece-card__title">{pieza.nombreRealMostrar}</h3>
                                <div className="collection-piece-card__actions">
                                    <FavoriteButton targetType={FAVORITE_TARGETS.PIECE} targetId={pieza.id} favoriteId={pieza.favoriteId} isFavorite={pieza.isFavorite} onChange={state => updatePieceFavorite(pieza.id, state)} />
                                    <button className="btn btn--outline btn--sm" style={{padding: '4px', minWidth: 'auto', border: 'none'}} aria-label={`Editar ${pieza.nombreRealMostrar}`} onClick={(e)=>{e.stopPropagation(); setEditPiezaModal({ open: true, pieza: pieza, nombre: pieza.nombreRealMostrar, condicion: pieza.condicion }); setImgPreview(pieza.imagenes?.[0] || pieza.imagenes?.[1] || null);}}><Icons.Edit /></button>
                                    <button className="btn btn--outline btn--sm" style={{padding: '4px', minWidth: 'auto', border: 'none', color: 'var(--vermilion)'}} aria-label={`Eliminar ${pieza.nombreRealMostrar}`} onClick={(e)=>{e.stopPropagation(); setDeletePiezaModal({ open: true, id: pieza.id, nombre: pieza.nombreRealMostrar });}}><Icons.Trash /></button>
                                </div>
                            </div>
                            <div className="card__seller">SKU: {pieza.sku || 'SIN SKU'}</div>
                            <div className="card__seller" style={{color: 'var(--sea)'}}>{pieza.condicion || 'NUEVA'}</div>
                        </div>
                    </div>
                    <button className="btn btn--outline btn--sm" style={{width:'100%', marginTop:'24px', justifyContent: 'center'}} onClick={(e)=>{e.stopPropagation(); setSaleTarget({ id: pieza.id, nombre: pieza.nombreRealMostrar }); dispatchSaleForm({ type: 'reset', initialCondition: pieza.condicion || 'NUEVA' });}}>
                        Vender en Marketplace
                    </button>
                </div>
            ) : (
                <div className="card collection-piece-card collection-piece-card--missing" key={`falt-${idx}`}>
                    <div className="card__media collection-piece-card__media collection-piece-card__placeholder">
                        <div className="h-3" style={{color: 'var(--ink-40)'}}>#{pieza.numero_ficticio || idx + 1}</div>
                    </div>
                    <div className="card__meta" style={{marginTop: '16px'}}>
                        <div>
                            <h3 className="card__title" style={{fontSize: '16px'}}>{pieza.nombre}</h3>
                            <div className="card__seller" style={{color: 'var(--vermilion)'}}>FALTANTE EN BÓVEDA</div>
                        </div>
                    </div>
                </div>
            )
        ))}
      </div>

      {}
      {saleTarget && (
          <div className="overlay-backdrop">
              <div className="overlay-panel overlay-panel--md" role="dialog" aria-modal="true" aria-label="Publicar pieza">
                  <button type="button" className="overlay-close" aria-label="Cerrar formulario de venta" onClick={cancelSaleModal} disabled={saleForm.submitting}><Icons.X /></button>
                  <div className="eyebrow" style={{marginBottom: '16px', color: 'var(--vermilion)'}}>NUEVA PUBLICACIÓN GLOBAL</div>
                  <h2 className="h-3" style={{marginBottom: '32px'}}>Vender {saleTarget.nombre}</h2>
                  <MarketplacePublicationForm
                    value={saleForm.data}
                    onChange={(field, value) => dispatchSaleForm({ type: 'change', field, value })}
                    onSubmit={handleVenderPieza}
                    onCancel={cancelSaleModal}
                    fieldErrors={saleForm.fieldErrors}
                    submitting={saleForm.submitting}
                    submitLabel="Publicar en Mercado"
                  />
              </div>
          </div>
      )}

      {editPiezaModal.open && (
          <div className="overlay-backdrop">
              <div className="overlay-panel overlay-panel--split" style={{ '--overlay-max-width': '600px' }} role="dialog" aria-modal="true" aria-label="Editar pieza">
                  <button type="button" className="overlay-close" aria-label="Cerrar edición de pieza" onClick={() => {setEditPiezaModal({ open: false, pieza: null, nombre: '', condicion: '' }); setImgPreview(null); setImagenArchivo(null);}}><Icons.X /></button>
                  <div>
                      <div className="eyebrow" style={{marginBottom: '12px'}}>FOTO REAL</div>
                      {!imgPreview ? (
                          <label style={{display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '32px 16px', border: '2px dashed var(--ink-20)', borderRadius: '12px', background: 'var(--paper-2)', cursor: 'pointer', color: 'var(--ink-60)', height: '200px', textAlign: 'center'}}><Icons.Image /><span style={{fontWeight: 'bold', color: 'var(--sea)', marginTop: '12px', fontSize: '14px'}}>Actualizar Foto</span><input type="file" style={{display: 'none'}} accept="image/*" onChange={handleImageUpload} /></label>
                      ) : (
                          <div style={{position: 'relative', borderRadius: '12px', overflow: 'hidden', border: '1px solid var(--ink-10)', height: '200px'}}><MediaImage sources={imgPreview} alt="Vista previa" fallback={<Icons.Image />} style={{width: '100%', height: '100%', objectFit: 'cover'}} /><button type="button" className="collection-media-remove" aria-label="Retirar fotografía" onClick={() => {setImgPreview(null); setImagenArchivo(null);}}><Icons.X /></button></div>
                      )}
                  </div>
                  <div>
                    <div className="eyebrow" style={{marginBottom: '16px', color: 'var(--sea)'}}>ACTUALIZAR INVENTARIO</div>
                    <h2 className="h-3" style={{marginBottom: '24px'}}>Editar Pieza</h2>
                    <div className="form-group" style={{marginBottom: '20px'}}><label className="eyebrow" style={{display: 'block', marginBottom: '8px'}}>NOMBRE</label><input type="text" className="editorial-input" style={{fontSize: '16px', padding: '8px 0'}} value={editPiezaModal.nombre} onChange={e => setEditPiezaModal({...editPiezaModal, nombre: e.target.value})} /></div>
                    <button className="btn btn--sea" style={{width: '100%', justifyContent: 'center', marginTop: '24px'}} onClick={handleEditarPieza}>Guardar Cambios</button>
                  </div>
              </div>
          </div>
      )}

      {deletePiezaModal.open && (
          <div className="overlay-backdrop">
              <div className="overlay-panel overlay-panel--sm overlay-panel--center" role="dialog" aria-modal="true" aria-label="Confirmar eliminación de pieza">
                  <div style={{width: '64px', height: '64px', borderRadius: '50%', background: 'var(--negative-surface)', color: 'var(--negative)', display: 'grid', placeItems: 'center', margin: '0 auto 24px auto'}}><Icons.Trash /></div>
                  <h2 className="h-3" style={{marginBottom: '16px'}}>¿Descartar Pieza?</h2>
                  <p style={{color: 'var(--ink-60)', marginBottom: '32px'}}>Eliminarás <strong>"{deletePiezaModal.nombre}"</strong> de tu inventario. Esta acción es irreversible.</p>
                  <div className="overlay-actions overlay-actions--center"><button className="btn btn--outline" onClick={() => setDeletePiezaModal({open: false, id: null, nombre: ''})}>Cancelar</button><button className="btn btn--vermilion" onClick={handleDeletePiezaConfirm}>Sí, Eliminar</button></div>
              </div>
          </div>
      )}
    </div>
  );
}
