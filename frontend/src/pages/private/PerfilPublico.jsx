import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import MediaImage from '../../components/MediaImage';
import ResourceState from '../../components/ResourceState';
import { AppError } from '../../services/errors';
import { loadProfileSummary } from '../../services/profiles';

export default function PerfilPublico() {
  const { profileId } = useParams();
  const API_URL = import.meta.env.VITE_API_URL;
  const [summary, setSummary] = useState(null);
  const [state, setState] = useState('loading');
  useEffect(() => { let active = true; loadProfileSummary(API_URL, profileId).then(data => { if (active) { setSummary(data); setState('ready'); } }).catch(error => { if (active) setState(error instanceof AppError && ['not_found', 'permission_denied'].includes(error.code) ? 'unavailable' : 'error'); }); return () => { active = false; }; }, [API_URL, profileId]);
  if (state !== 'ready') return <ResourceState type={state} backTo="/app/comunidad" backLabel="Volver a Comunidad" />;
  const { profile, estadisticas, colecciones, resenas } = summary;
  return <div className="profile-page profile-page--public"><header className="profile-page__identity"><MediaImage sources={profile.avatar} alt={`Avatar de ${profile.user.nombre}`} fallback={profile.user.nombre[0]?.toUpperCase()} className="profile-page__avatar" /><div className="profile-page__identity-copy"><div className="eyebrow">PERFIL PÚBLICO</div><h1>{profile.user.nombre}</h1><p>{profile.biografia || 'Este coleccionista aún no ha añadido una biografía.'}</p><p>{profile.ubicacion || 'Sin ubicación pública registrada'}</p></div></header><section><h2>Resumen público</h2><div className="profile-stats"><div className="profile-stat"><span>Piezas públicas</span><strong>{estadisticas.piezas_publicas}</strong></div><div className="profile-stat"><span>Colecciones visibles</span><strong>{estadisticas.colecciones}</strong></div><div className="profile-stat"><span>Likes recibidos</span><strong>{estadisticas.likes_recibidos}</strong></div><div className="profile-stat"><span>Ventas completadas</span><strong>{estadisticas.ventas_completadas}</strong></div><div className="profile-stat"><span>Valoración</span><strong>{estadisticas.promedio_resenas ? `${Number(estadisticas.promedio_resenas).toFixed(1)}/5 (${estadisticas.cantidad_resenas})` : 'Sin reseñas'}</strong></div></div></section><section className="profile-public-list"><h2>Colecciones con piezas públicas</h2>{colecciones.results.length ? <ul>{colecciones.results.map(item => <li key={item.id}>{item.nombre}: {item.piezas} piezas públicas</li>)}</ul> : <p>Sin colecciones públicas visibles.</p>}</section><section className="profile-public-list"><h2>Reseñas recibidas</h2>{resenas.recibidas.results.length ? <ul>{resenas.recibidas.results.map(item => <li key={item.id}><strong>{item.autor.nombre} · {item.puntuacion}/5</strong><p>{item.comentario}</p></li>)}</ul> : <p>Sin reseñas recibidas.</p>}</section></div>;
}
