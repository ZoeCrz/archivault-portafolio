import { useEffect, useState } from 'react';
import { Link, useOutletContext, useParams } from 'react-router-dom';
import MediaImage from '../../components/MediaImage';
import ResourceState from '../../components/ResourceState';
import { apiRequest } from '../../services/api';
import { AppError, notifyApiError } from '../../services/errors';
import { resourceRoutes } from '../../services/routes';

const list = data => Array.isArray(data) ? data : data?.results || [];

export default function DetallePost() {
  const { postId } = useParams();
  const { addNotification } = useOutletContext();
  const [data, setData] = useState(null);
  const [comment, setComment] = useState('');
  const [resourceError, setResourceError] = useState(null);
  const API_URL = import.meta.env.VITE_API_URL;
  const currentUserId = Number.parseInt(localStorage.getItem('archivault_user_id'), 10);

  const load = async () => {
    try {
      const [post, media, comments, likes, users, profiles] = await Promise.all([
        apiRequest(`${API_URL}/api/v1/community/posts/${postId}/`),
        apiRequest(`${API_URL}/api/v1/community/media/`),
        apiRequest(`${API_URL}/api/v1/community/comentarios/`),
        apiRequest(`${API_URL}/api/v1/community/likes/`),
        apiRequest(`${API_URL}/api/v1/accounts/users/`),
        apiRequest(`${API_URL}/api/v1/accounts/profiles/`),
      ]);
      const usersById = Object.fromEntries(list(users).map(user => [user.id, user]));
      const profilesByUser = Object.fromEntries(list(profiles).map(profile => [profile.user, profile]));
      setData({ post, media: list(media).filter(item => item.post === post.id), comments: list(comments).filter(item => item.post === post.id), likes: list(likes).filter(item => item.post === post.id), usersById, profilesByUser });
    } catch (error) {
      setResourceError(error instanceof AppError && ['not_found', 'permission_denied'].includes(error.code) ? 'unavailable' : 'error');
    }
  };

  useEffect(() => {
    // Data is loaded from the resource identified by the route.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    load();
  }, [postId]); // eslint-disable-line react-hooks/exhaustive-deps

  const toggleLike = async () => {
    const ownLike = data.likes.find(like => like.user === currentUserId);
    try {
      if (ownLike) await apiRequest(`${API_URL}/api/v1/community/likes/${ownLike.id}/`, { method: 'DELETE' });
      else await apiRequest(`${API_URL}/api/v1/community/likes/`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ post: data.post.id }) });
      await load();
    } catch (error) { notifyApiError(addNotification, error, 'No se pudo actualizar la reacción'); }
  };

  const submitComment = async event => {
    event.preventDefault();
    if (!comment.trim()) return;
    try {
      await apiRequest(`${API_URL}/api/v1/community/comentarios/`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ post: data.post.id, contenido: comment.trim() }) });
      setComment('');
      await load();
    } catch (error) { notifyApiError(addNotification, error, 'No se pudo publicar el comentario'); }
  };

  if (resourceError) return <ResourceState type={resourceError} backTo="/app/comunidad" backLabel="Volver a Comunidad" />;
  if (!data) return <ResourceState type="loading" />;
  const author = data.usersById[data.post.user];
  const authorProfile = data.profilesByUser[data.post.user];
  return (
    <div className="view-container" style={{ maxWidth: '760px', width: '100%', margin: '0 auto', padding: '64px 24px' }}>
      <article style={{ background: 'var(--surface)', borderRadius: '16px', border: '1px solid var(--ink-20)', overflow: 'hidden' }}>
        <div style={{ padding: '32px' }}>
          {authorProfile ? <Link to={resourceRoutes.profile(authorProfile.id)} style={{ fontFamily: 'var(--serif)', fontWeight: 'bold', color: 'var(--ink)' }}>{author?.username || 'Coleccionista'}</Link> : <strong>{author?.username || 'Coleccionista'}</strong>}
          <p style={{ fontSize: '20px', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>{data.post.contenido}</p>
          {data.media.length > 0 && <MediaImage sources={data.media.flatMap(item => [item.archivo, item.url])} alt="Contenido adjunto" fallback={<div>Imagen no disponible</div>} style={{ width: '100%', borderRadius: '12px' }} />}
        </div>
        <div style={{ padding: '16px 32px', borderTop: '1px solid var(--ink-10)' }}><button className="btn btn--outline" onClick={toggleLike}>{data.likes.some(like => like.user === currentUserId) ? 'Quitar reacción' : 'Reaccionar'} · {data.likes.length}</button></div>
        <div style={{ padding: '32px', background: 'var(--paper-2)' }}>
          {data.comments.map(item => <div key={item.id} style={{ marginBottom: '16px' }}><strong>{data.usersById[item.user]?.username || 'Coleccionista'}</strong><p>{item.contenido}</p>{item.imagen && <MediaImage sources={item.imagen} alt="Imagen del comentario" fallback={null} style={{ maxWidth: '100%', borderRadius: '8px' }} />}</div>)}
          <form onSubmit={submitComment} style={{ display: 'flex', gap: '12px' }}><input className="editorial-input" value={comment} onChange={event => setComment(event.target.value)} placeholder="Añade a la discusión..." /><button className="btn btn--ink">Responder</button></form>
        </div>
      </article>
    </div>
  );
}
