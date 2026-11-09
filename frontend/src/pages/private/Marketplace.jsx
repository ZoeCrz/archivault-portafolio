import { useEffect, useRef, useState } from 'react';
import { useOutletContext, useSearchParams } from 'react-router-dom';
import MarketplacePublicationSummary from '../../components/MarketplacePublicationSummary';
import { apiRequest } from '../../services/api';
import { notifyApiError } from '../../services/errors';
import {
  MARKETPLACE_DEFAULT_ORDER,
  marketplaceApiQuery,
  normalizeMarketplacePage,
  updateMarketplaceParams,
} from '../../services/marketplaceFilters';

const Icons = {
  MessageCircle: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" /></svg>,
};

const emptyPage = { count: 0, next: null, previous: null, results: [] };

export default function Marketplace() {
  const { openChatWithUser, addNotification } = useOutletContext() || {};
  const [searchParams, setSearchParams] = useSearchParams();
  const searchString = searchParams.toString();
  const searchTimer = useRef(null);
  const searchInput = useRef(null);
  const [publications, setPublications] = useState(emptyPage);
  const [offers, setOffers] = useState([]);
  const [offerModal, setOfferModal] = useState({ open: false, publicacionId: null, nombre: '', monto: '' });
  const [reloadKey, setReloadKey] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const API_URL = import.meta.env.VITE_API_URL;
  const currentUserId = Number.parseInt(localStorage.getItem('archivault_user_id'), 10);

  useEffect(() => () => window.clearTimeout(searchTimer.current), []);

  useEffect(() => {
    if (searchInput.current) searchInput.current.value = searchParams.get('q') || '';
  }, [searchString, searchParams]);

  useEffect(() => {
    let active = true;
    const fetchData = async () => {
      setLoading(true);
      setLoadError(false);
      try {
        const query = marketplaceApiQuery(searchParams);
        const [publicationData, offerData] = await Promise.all([
          apiRequest(`${API_URL}/api/v1/marketplace/publicaciones/${query ? `?${query}` : ''}`),
          apiRequest(`${API_URL}/api/v1/marketplace/ofertas/`),
        ]);
        if (active) {
          setPublications(normalizeMarketplacePage(publicationData));
          setOffers(Array.isArray(offerData) ? offerData : offerData?.results || []);
        }
      } catch (error) {
        if (active) {
          setLoadError(true);
          notifyApiError(addNotification, error, 'No se pudo cargar el marketplace');
        }
      } finally {
        if (active) setLoading(false);
      }
    };
    fetchData();
    return () => { active = false; };
  }, [API_URL, addNotification, reloadKey, searchString, searchParams]);

  const updateFilter = (name, value) => {
    setSearchParams(updateMarketplaceParams(searchParams, { [name]: value }));
  };

  const updateSearch = value => {
    window.clearTimeout(searchTimer.current);
    searchTimer.current = window.setTimeout(() => {
      setSearchParams(updateMarketplaceParams(searchParams, { q: value }));
    }, 350);
  };

  const handleCrearOferta = async () => {
    if (!offerModal.monto || !offerModal.publicacionId) return;
    try {
      await apiRequest(`${API_URL}/api/v1/marketplace/ofertas/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ publicacion: offerModal.publicacionId, monto: offerModal.monto }),
      });
      addNotification('Oferta enviada', 'El vendedor recibió tu propuesta.', 'success');
      setOfferModal({ open: false, publicacionId: null, nombre: '', monto: '' });
      setReloadKey(key => key + 1);
    } catch (error) {
      notifyApiError(addNotification, error, 'No se pudo enviar la oferta');
    }
  };

  const handleOfferAction = async (offerId, action) => {
    try {
      await apiRequest(`${API_URL}/api/v1/marketplace/ofertas/${offerId}/${action}/`, { method: 'POST' });
      const labels = { aceptar: 'Oferta aceptada', rechazar: 'Oferta rechazada', completar: 'Venta completada' };
      addNotification('Marketplace', labels[action], 'success');
      setReloadKey(key => key + 1);
    } catch (error) {
      notifyApiError(addNotification, error, 'No se pudo actualizar la oferta');
    }
  };

  const goToPage = page => setSearchParams(updateMarketplaceParams(searchParams, { page }));
  const currentPage = Number.parseInt(searchParams.get('page') || '1', 10);
  const updatePublicationFavorite = (publicationId, favoriteState) => {
    setPublications(previous => {
      if (searchParams.get('favoritos') === 'true' && !favoriteState.isFavorite) {
        return {
          ...previous,
          count: Math.max(0, previous.count - 1),
          results: previous.results.filter(item => item.id !== publicationId),
        };
      }
      return {
        ...previous,
        results: previous.results.map(item => item.id === publicationId
          ? { ...item, es_favorito: favoriteState.isFavorite }
          : item),
      };
    });
  };

  return (
    <div className="view-container layout-container layout-container--wide marketplace-page">
      <div className="split-hero marketplace-page__hero">
        <div className="hero-text marketplace-page__hero-copy">
          <div className="eyebrow" style={{ marginBottom: '24px' }}>MERCADO GLOBAL</div>
          <h1 className="h-display marketplace-page__title">Encuentra el <em style={{ color: 'var(--vermilion)' }}>eslabón</em> perdido.</h1>
          <p style={{ fontSize: '18px', marginTop: '24px', color: 'var(--ink-60)', lineHeight: 1.6 }}>Explora piezas y colecciones publicadas por la comunidad.</p>
        </div>
      </div>

      <div className="marketplace-page__content layout-section">
        <div className="layout-sidebar marketplace-page__layout">
          <aside className="marketplace-page__sidebar">
            <div className="marketplace-filters">
              <div className="eyebrow">FILTROS DEL MERCADO</div>
              <label>Buscar<input ref={searchInput} className="editorial-input" defaultValue={searchParams.get('q') || ''} onChange={event => updateSearch(event.target.value)} placeholder="Nombre, SKU o colección" /></label>
              <label>Tipo<select className="editorial-input" value={searchParams.get('tipo') || ''} onChange={event => updateFilter('tipo', event.target.value)}><option value="">Todos</option><option value="PIEZA">Piezas</option><option value="COLECCION">Colecciones</option></select></label>
              <label>Estado<select className="editorial-input" value={searchParams.get('estado') || ''} onChange={event => updateFilter('estado', event.target.value)}><option value="">Todos los visibles</option><option value="ACTIVA">Activa</option><option value="RESERVADA">Reservada</option><option value="VENDIDA">Vendida</option><option value="CANCELADA">Cancelada</option></select></label>
              <label>Condición<select className="editorial-input" value={searchParams.get('condicion') || ''} onChange={event => updateFilter('condicion', event.target.value)}><option value="">Todas</option><option value="NUEVA">Nueva</option><option value="USADA">Usada</option><option value="DAÑADA">Dañada</option><option value="NO_ESPECIFICADA">No especificada</option></select></label>
              <label>Categoría<input className="editorial-input" value={searchParams.get('categoria') || ''} onChange={event => updateFilter('categoria', event.target.value)} placeholder="Categoría exacta" /></label>
              <label>Colección<input className="editorial-input" type="number" min="1" value={searchParams.get('coleccion') || ''} onChange={event => updateFilter('coleccion', event.target.value)} placeholder="ID de colección" /></label>
              <label>Precio mínimo<input className="editorial-input" type="number" min="0" step="0.01" value={searchParams.get('precio_min') || ''} onChange={event => updateFilter('precio_min', event.target.value)} /></label>
              <label>Precio máximo<input className="editorial-input" type="number" min="0" step="0.01" value={searchParams.get('precio_max') || ''} onChange={event => updateFilter('precio_max', event.target.value)} /></label>
              <label>Orden<select className="editorial-input" value={searchParams.get('orden') || MARKETPLACE_DEFAULT_ORDER} onChange={event => updateFilter('orden', event.target.value)}><option value="recientes">Más recientes</option><option value="antiguos">Más antiguos</option><option value="precio_asc">Menor precio</option><option value="precio_desc">Mayor precio</option><option value="nombre_asc">Nombre</option></select></label>
              <label className="marketplace-filters__favorite"><input type="checkbox" checked={searchParams.get('favoritos') === 'true'} onChange={event => updateFilter('favoritos', event.target.checked ? 'true' : '')} /> Sólo favoritos</label>
            </div>
          </aside>

          <div className="marketplace-page__results">
            {loading && <div className="marketplace-state">Cargando publicaciones…</div>}
            {!loading && loadError && <div className="marketplace-state"><p>No pudimos cargar las publicaciones.</p><button className="btn btn--outline" onClick={() => setReloadKey(key => key + 1)}>Intentar nuevamente</button></div>}
            {!loading && !loadError && publications.results.length === 0 && <div className="marketplace-state marketplace-state--empty"><h3 className="h-3">Sin resultados</h3><p>No hay publicaciones que coincidan con los filtros actuales.</p></div>}
            {!loading && !loadError && publications.results.length > 0 && <div className="layout-grid marketplace-results-grid">
              {publications.results.map(publication => {
                const publicationOffers = offers.filter(item => item.publicacion === publication.id);
                const ownOffer = publicationOffers.find(item => item.comprador === currentUserId);
                const isSeller = publication.vendedor?.id === currentUserId;
                return <div className="card marketplace-card" key={publication.id}>
                  <MarketplacePublicationSummary publication={publication} linked onFavoriteChange={state => updatePublicationFavorite(publication.id, state)} />
                  {isSeller ? <div className="marketplace-card__offers">
                    <div className="eyebrow">OFERTAS RECIBIDAS</div>
                    {publicationOffers.length === 0 ? <p>Aún no hay propuestas.</p> : publicationOffers.map(item => <div key={item.id} className="marketplace-card__offer"><strong>${item.monto}</strong> · {item.estado}{item.estado === 'PENDIENTE' && <div className="layout-cluster marketplace-card__offer-actions"><button className="btn btn--sea btn--sm" onClick={() => handleOfferAction(item.id, 'aceptar')}>Aceptar</button><button className="btn btn--outline btn--sm" onClick={() => handleOfferAction(item.id, 'rechazar')}>Rechazar</button></div>}{item.estado === 'ACEPTADA' && <button className="btn btn--vermilion btn--sm" onClick={() => handleOfferAction(item.id, 'completar')}>Completar venta</button>}</div>)}
                  </div> : <div className="marketplace-card__actions">{ownOffer ? <div className="chip">TU OFERTA: ${ownOffer.monto} · {ownOffer.estado}</div> : publication.estado === 'ACTIVA' && <button className="btn btn--vermilion" onClick={() => setOfferModal({ open: true, publicacionId: publication.id, nombre: publication.nombre, monto: publication.precio })}>Hacer una oferta</button>}<button className="btn btn--ink" onClick={() => openChatWithUser(publication.vendedor.id, publication.vendedor.nombre)}><Icons.MessageCircle /> Contactar al vendedor</button></div>}
                </div>;
              })}
            </div>}

            {!loading && !loadError && publications.count > 0 && <nav aria-label="Paginación del marketplace" className="marketplace-pagination"><button className="btn btn--outline" disabled={!publications.previous} onClick={() => goToPage(currentPage - 1)}>Anterior</button><span>Página {currentPage} · {publications.count} resultados</span><button className="btn btn--outline" disabled={!publications.next} onClick={() => goToPage(currentPage + 1)}>Siguiente</button></nav>}
          </div>
        </div>
      </div>

      {offerModal.open && <div className="overlay-backdrop overlay-backdrop--priority"><div className="overlay-panel overlay-panel--offer" role="dialog" aria-modal="true" aria-label="Nueva oferta"><div className="eyebrow">NUEVA OFERTA</div><h2 className="h-3">{offerModal.nombre}</h2><label>MONTO (MXN)<input type="number" min="0.01" step="0.01" className="editorial-input" value={offerModal.monto} onChange={event => setOfferModal({ ...offerModal, monto: event.target.value })} /></label><div className="overlay-actions" style={{ marginTop: '28px' }}><button className="btn btn--outline" onClick={() => setOfferModal({ open: false, publicacionId: null, nombre: '', monto: '' })}>Cancelar</button><button className="btn btn--vermilion" onClick={handleCrearOferta}>Enviar oferta</button></div></div></div>}
    </div>
  );
}
