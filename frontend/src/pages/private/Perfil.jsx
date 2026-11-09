import { useEffect, useState } from 'react';
import { Link, useOutletContext } from 'react-router-dom';
import MediaImage from '../../components/MediaImage';
import ResourceState from '../../components/ResourceState';
import { apiRequest } from '../../services/api';
import { notifyApiError } from '../../services/errors';
import { biographyCount, loadProfileActivity, loadProfileSummary } from '../../services/profiles';

const ACTIVITY_TYPES = ['likes_realizados', 'likes_recibidos', 'ventas', 'resenas_hechas', 'resenas_recibidas'];
const LABELS = { likes_realizados: 'Likes realizados', likes_recibidos: 'Likes recibidos', ventas: 'Ventas completadas', resenas_hechas: 'Reseñas hechas', resenas_recibidas: 'Reseñas recibidas' };

async function fetchProfileData(apiUrl, userId) {
  const profiles = await apiRequest(`${apiUrl}/api/v1/accounts/profiles/`);
  const own = (Array.isArray(profiles) ? profiles : profiles.results || []).find(item => item.user === userId);
  if (!own) throw new Error('profile_missing');
  const summary = await loadProfileSummary(apiUrl, own.id);
  const activityResults = await Promise.all(ACTIVITY_TYPES.map(type => loadProfileActivity(apiUrl, own.id, type)));
  return { summary, activities: Object.fromEntries(ACTIVITY_TYPES.map((type, index) => [type, activityResults[index]])) };
}

function StatCard({ label, value }) {
  return <div className="profile-stat"><span>{label}</span><strong>{value ?? 0}</strong></div>;
}

function ActivityList({ type, data, onMore }) {
  const items = data?.results || [];
  return <section className="profile-activity"><h2>{LABELS[type]}</h2><p className="profile-activity__note">Lista de actividad sin orden cronológico.</p>{items.length === 0 ? <p>Sin elementos.</p> : <ul>{items.map(item => <li key={item.id}><strong>{item.nombre || item.usuario?.nombre || `Publicación ${item.post_id}`}</strong>{item.puntuacion ? ` · ${item.puntuacion}/5` : ''}{item.comentario && <p>{item.comentario}</p>}{item.post_contenido && <p>{item.post_contenido}</p>}</li>)}</ul>}{data?.next && <button type="button" className="btn btn--outline btn--sm" onClick={onMore}>Cargar más</button>}</section>;
}

export default function Perfil() {
  const { addNotification } = useOutletContext();
  const userId = Number(localStorage.getItem('archivault_user_id'));
  const API_URL = import.meta.env.VITE_API_URL;
  const [summary, setSummary] = useState(null);
  const [activities, setActivities] = useState({});
  const [activityPages, setActivityPages] = useState({});
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState({ biografia: '', ubicacion: '', perfil_publico: true });
  const [avatarFile, setAvatarFile] = useState(null);
  const [error, setError] = useState(false);

  const applyProfileData = data => {
    setSummary(data.summary);
    setDraft({ biografia: data.summary.profile.biografia || '', ubicacion: data.summary.profile.ubicacion || '', perfil_publico: data.summary.profile.perfil_publico });
    setActivities(data.activities);
    setActivityPages(Object.fromEntries(ACTIVITY_TYPES.map(type => [type, 1])));
    setError(false);
  };

  useEffect(() => {
    let active = true;
    fetchProfileData(API_URL, userId).then(data => {
      if (active) applyProfileData(data);
    }).catch(loadError => {
      if (active) {
        setError(true);
        notifyApiError(addNotification, loadError, 'No se pudo cargar el perfil');
      }
    });
    return () => { active = false; };
  }, [API_URL, addNotification, userId]);

  const save = async () => {
    try {
      const body = new FormData();
      body.append('biografia', draft.biografia.trim());
      body.append('ubicacion', draft.ubicacion.trim());
      body.append('perfil_publico', String(draft.perfil_publico));
      if (avatarFile) body.append('avatar', avatarFile);
      await apiRequest(`${API_URL}/api/v1/accounts/profiles/${summary.profile.id}/`, { method: 'PATCH', body });
      setEditing(false); setAvatarFile(null); applyProfileData(await fetchProfileData(API_URL, userId));
      addNotification('Perfil actualizado', 'Los cambios se guardaron correctamente.', 'success');
    } catch (saveError) { notifyApiError(addNotification, saveError, 'No se pudo actualizar el perfil'); }
  };

  const loadMore = async type => {
    try {
      const page = (activityPages[type] || 1) + 1;
      const next = await loadProfileActivity(API_URL, summary.profile.id, type, page);
      setActivities(previous => ({ ...previous, [type]: { ...next, results: [...previous[type].results, ...next.results] } }));
      setActivityPages(previous => ({ ...previous, [type]: page }));
    } catch (loadError) {
      notifyApiError(addNotification, loadError, 'No se pudo cargar más actividad');
    }
  };

  if (error) return <ResourceState type="error" />;
  if (!summary) return <ResourceState type="loading" />;
  const { profile, estadisticas, distribuciones, colecciones } = summary;
  return <div className="profile-page">
    <header className="profile-page__identity"><MediaImage sources={profile.avatar} alt={`Avatar de ${profile.user.nombre}`} fallback={profile.user.nombre[0]?.toUpperCase()} className="profile-page__avatar" /><div className="profile-page__identity-copy"><div className="eyebrow">MI PERFIL</div><h1>{profile.user.nombre}</h1><p>{profile.biografia || 'Añade una biografía para presentarte a la comunidad.'}</p><p>{profile.ubicacion || 'Sin ubicación registrada'}</p></div><button type="button" className="btn btn--outline" onClick={() => setEditing(true)}>Editar perfil</button></header>
    {editing && <section className="profile-editor"><label>Biografía<textarea maxLength="500" value={draft.biografia} onChange={event => setDraft({ ...draft, biografia: event.target.value })} /></label><small>{biographyCount(draft.biografia)}/500</small><label>Ubicación<input value={draft.ubicacion} onChange={event => setDraft({ ...draft, ubicacion: event.target.value })} /></label><label><input type="checkbox" checked={draft.perfil_publico} onChange={event => setDraft({ ...draft, perfil_publico: event.target.checked })} /> Perfil público</label><label>Avatar<input type="file" accept="image/*" onChange={event => setAvatarFile(event.target.files?.[0] || null)} /></label><div><button type="button" className="btn btn--outline" onClick={() => setEditing(false)}>Cancelar</button><button type="button" className="btn btn--vermilion" onClick={save}>Guardar</button></div></section>}
    <section><h2>Estadísticas</h2><div className="profile-stats"><StatCard label="Piezas" value={estadisticas.piezas_registradas} /><StatCard label="Colecciones" value={estadisticas.colecciones} /><StatCard label="Likes realizados" value={estadisticas.likes_realizados} /><StatCard label="Likes recibidos" value={estadisticas.likes_recibidos} /><StatCard label="Ventas completadas" value={estadisticas.ventas_completadas} /><StatCard label="Valoración" value={estadisticas.promedio_resenas ? `${Number(estadisticas.promedio_resenas).toFixed(1)}/5 (${estadisticas.cantidad_resenas})` : 'Sin reseñas'} /></div></section>
    <section><h2>Inventario por estado</h2>{Object.entries(distribuciones.inventario_por_estado).map(([key, value]) => <div className="profile-bar" key={key}><span>{key === 'ADQUIRIDA' ? 'Adquiridas' : 'Deseadas'}: {value}</span><div><i style={{ width: `${estadisticas.piezas_registradas ? value / estadisticas.piezas_registradas * 100 : 0}%` }} /></div></div>)}</section>
    <section><h2>Progreso de colecciones</h2>{colecciones.results.map(item => <div className="profile-bar" key={item.coleccion_usuario_id}><span><Link to={`/app/colecciones/${item.coleccion_usuario_id}`}>{item.nombre}</Link>: {item.progreso}%</span><div><i style={{ width: `${item.progreso}%` }} /></div></div>)}</section>
    <section><h2>Distribución de reseñas</h2>{Object.entries(distribuciones.resenas_por_puntuacion).reverse().map(([score, value]) => <div className="profile-bar" key={score}><span>{score} estrellas: {value}</span><div><i style={{ width: `${estadisticas.cantidad_resenas ? value / estadisticas.cantidad_resenas * 100 : 0}%` }} /></div></div>)}</section>
    <div className="profile-activities">{ACTIVITY_TYPES.map(type => <ActivityList key={type} type={type} data={activities[type]} onMore={() => loadMore(type)} />)}</div>
  </div>;
}
