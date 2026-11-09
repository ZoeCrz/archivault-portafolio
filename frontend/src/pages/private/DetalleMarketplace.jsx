import { useEffect, useState } from 'react';
import { useOutletContext, useParams } from 'react-router-dom';
import MarketplacePublicationSummary from '../../components/MarketplacePublicationSummary';
import ResourceState from '../../components/ResourceState';
import { apiRequest } from '../../services/api';
import { AppError, notifyApiError } from '../../services/errors';
import { loadMarketplacePublication } from '../../services/marketplace';

export default function DetalleMarketplace() {
  const { publicacionId } = useParams();
  const { addNotification, openChatWithUser } = useOutletContext();
  const [publication, setPublication] = useState(null);
  const [offers, setOffers] = useState([]);
  const [amount, setAmount] = useState('');
  const [resourceError, setResourceError] = useState(null);
  const API_URL = import.meta.env.VITE_API_URL;
  const currentUserId = Number.parseInt(localStorage.getItem('archivault_user_id'), 10);

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const [item, offerData] = await Promise.all([
          loadMarketplacePublication(API_URL, publicacionId),
          apiRequest(`${API_URL}/api/v1/marketplace/ofertas/`),
        ]);
        if (active) {
          setPublication(item);
          setAmount(item.precio || '');
          setOffers((Array.isArray(offerData) ? offerData : offerData.results || []).filter(offer => offer.publicacion === item.id));
        }
      } catch (error) {
        if (active) setResourceError(error instanceof AppError && ['not_found', 'permission_denied'].includes(error.code) ? 'unavailable' : 'error');
      }
    };
    load();
    return () => { active = false; };
  }, [API_URL, publicacionId]);

  const createOffer = async () => {
    try {
      const offer = await apiRequest(`${API_URL}/api/v1/marketplace/ofertas/`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ publicacion: publication.id, monto: amount }),
      });
      setOffers(previous => [...previous, offer]);
      addNotification('Oferta enviada', 'El vendedor recibió tu propuesta.', 'success');
    } catch (error) { notifyApiError(addNotification, error, 'No se pudo enviar la oferta'); }
  };

  const updateOffer = async (offerId, action) => {
    try {
      const updated = await apiRequest(`${API_URL}/api/v1/marketplace/ofertas/${offerId}/${action}/`, { method: 'POST' });
      setOffers(previous => previous.map(offer => offer.id === updated.id ? updated : offer));
      const labels = { aceptar: 'Oferta aceptada', rechazar: 'Oferta rechazada', completar: 'Venta completada' };
      addNotification('Marketplace', labels[action], 'success');
      if (action !== 'rechazar') {
        setPublication(previous => ({ ...previous, estado: action === 'aceptar' ? 'RESERVADA' : 'VENDIDA' }));
      }
    } catch (error) { notifyApiError(addNotification, error, 'No se pudo actualizar la oferta'); }
  };

  if (resourceError) return <ResourceState type={resourceError} backTo="/app/marketplace" backLabel="Volver al marketplace" />;
  if (!publication) return <ResourceState type="loading" />;

  const ownPublication = publication.vendedor?.id === currentUserId;
  const ownOffer = offers.find(offer => offer.comprador === currentUserId);
  return (
    <div className="view-container" style={{ maxWidth: '760px', width: '100%', margin: '0 auto', padding: '64px 24px' }}>
      <div className="card" style={{ background: 'var(--paper)', padding: '24px', border: '1px solid var(--ink-10)', borderRadius: '16px' }}>
        <MarketplacePublicationSummary publication={publication} onFavoriteChange={state => setPublication(previous => ({ ...previous, es_favorito: state.isFavorite }))} />
        {!['ACTIVA', 'RESERVADA'].includes(publication.estado) && <p style={{ marginTop: '20px' }}>Esta publicación ya no está disponible para nuevas ofertas.</p>}
        {!ownPublication && publication.estado === 'ACTIVA' && !ownOffer && <div style={{ display: 'flex', gap: '12px', marginTop: '20px' }}><input className="editorial-input" type="number" min="0.01" step="0.01" value={amount} onChange={event => setAmount(event.target.value)} /><button className="btn btn--vermilion" onClick={createOffer}>Hacer oferta</button></div>}
        {ownOffer && <div className="chip" style={{ marginTop: '20px' }}>TU OFERTA: ${ownOffer.monto} · {ownOffer.estado}</div>}
        {ownPublication && <div style={{ marginTop: '24px', borderTop: '1px solid var(--ink-10)', paddingTop: '20px' }}>
          <div className="eyebrow" style={{ marginBottom: '12px' }}>OFERTAS RECIBIDAS</div>
          {offers.length === 0 ? <p>Aún no hay propuestas.</p> : offers.map(offer => <div key={offer.id} style={{ padding: '12px 0', borderBottom: '1px solid var(--ink-10)' }}>
            <strong>${offer.monto}</strong> · {offer.estado}
            {offer.estado === 'PENDIENTE' && <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}><button className="btn btn--sea btn--sm" onClick={() => updateOffer(offer.id, 'aceptar')}>Aceptar</button><button className="btn btn--outline btn--sm" onClick={() => updateOffer(offer.id, 'rechazar')}>Rechazar</button></div>}
            {offer.estado === 'ACEPTADA' && <button className="btn btn--vermilion btn--sm" style={{ marginTop: '8px' }} onClick={() => updateOffer(offer.id, 'completar')}>Completar venta</button>}
          </div>)}
        </div>}
        {!ownPublication && <button className="btn btn--ink" style={{ marginTop: '12px' }} onClick={() => openChatWithUser(publication.vendedor?.id, publication.vendedor?.nombre)}>Contactar al vendedor</button>}
      </div>
    </div>
  );
}
