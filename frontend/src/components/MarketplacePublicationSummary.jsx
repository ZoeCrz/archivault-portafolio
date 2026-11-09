import { Link } from 'react-router-dom';
import MediaImage from './MediaImage';
import FavoriteButton from './FavoriteButton';
import { resourceRoutes } from '../services/routes';
import { FAVORITE_TARGETS } from '../services/favorites';

export default function MarketplacePublicationSummary({ publication, linked = false, onFavoriteChange }) {
  const title = publication.nombre || 'Artículo exclusivo';
  const heading = linked
    ? <Link to={resourceRoutes.marketplacePublication(publication.id)} style={{ color: 'inherit', textDecoration: 'none' }}>{title}</Link>
    : title;

  return (
    <>
      <div className="card__media ph ph--sea marketplace-summary__media">
        <div className="badge chip chip--vermilion" style={{ top: '8px', left: '8px' }}>{publication.estado}</div>
        <div className="marketplace-summary__favorite">
          <FavoriteButton
            targetType={publication.tipo === 'COLECCION' ? FAVORITE_TARGETS.COLLECTION : FAVORITE_TARGETS.PIECE}
            targetId={publication.tipo === 'COLECCION' ? publication.coleccion?.id : publication.objetivo_id}
            isFavorite={publication.es_favorito}
            onChange={onFavoriteChange}
          />
        </div>
        <MediaImage sources={publication.imagen} alt={title} fallback={<div className="ph__label">{publication.tipo === 'COLECCION' ? 'COLECCIÓN' : 'PIEZA'}</div>} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
      </div>
      <div className="card__meta marketplace-summary__content">
        <div style={{ width: '100%' }}>
          <h3 className="card__title marketplace-summary__title">{heading}</h3>
          <div className="marketplace-summary__seller-price">
            <div className="card__seller" style={{ color: 'var(--ink)' }}>VENDEDOR:<br /><strong>{publication.vendedor?.nombre || 'Coleccionista verificado'}</strong></div>
            <div style={{ fontFamily: 'var(--mono)', fontWeight: 'bold', color: 'var(--vermilion)', fontSize: '20px' }}>${publication.precio || '0'}</div>
          </div>
          <div className="card__seller" style={{ color: 'var(--sea)' }}>CONDICIÓN:<br />{publication.condicion === 'NO_ESPECIFICADA' ? 'No especificada' : publication.condicion}</div>
        </div>
        <div className="marketplace-summary__description">
          {publication.descripcion || (publication.tipo === 'PIEZA' ? `SKU: ${publication.sku || 'Sin SKU'}` : 'Publicación histórica sin descripción.')}
        </div>
        <div className="card__seller" style={{ color: 'var(--ink-60)' }}>COLECCIÓN: {publication.coleccion?.nombre || 'Sin colección'}</div>
      </div>
    </>
  );
}
