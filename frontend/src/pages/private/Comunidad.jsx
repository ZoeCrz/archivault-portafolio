import { useState, useEffect, useCallback } from 'react';
import { Link, useOutletContext } from 'react-router-dom';
import MediaImage from '../../components/MediaImage';
import { apiRequest } from '../../services/api';
import { logTechnicalError, notifyApiError } from '../../services/errors';
import { resourceRoutes } from '../../services/routes';
import { loadCommunitySummary, normalizeCommunitySummary } from '../../services/community';

const Icons = {
  Image: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>,
  Close: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>,
  Heart: ({ filled }) => <svg width="22" height="22" viewBox="0 0 24 24" fill={filled ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path></svg>,
  MessageCircle: () => <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path></svg>
};

export default function Comunidad() {
  const { addNotification } = useOutletContext() || { addNotification: () => {} };
  
  const [posts, setPosts] = useState([]);
  const [comentarios, setComentarios] = useState([]);
  const [likes, setLikes] = useState([]);
  const [usersMap, setUsersMap] = useState({});
  const [avatarsMap, setAvatarsMap] = useState({});
  const [novedadesMkt, setNovedadesMkt] = useState([]);
  const [topUsers, setTopUsers] = useState([]);
  const [summaryError, setSummaryError] = useState(false);
  const [loading, setLoading] = useState(true);
  
  const [nuevoContenido, setNuevoContenido] = useState('');
  const [imagenPost, setImagenPost] = useState(null);
  const [imgPreview, setImgPreview] = useState(null);
  const [publicando, setPublicando] = useState(false);
  const [comentariosTextos, setComentariosTextos] = useState({});
  const [comentarioImgs, setComentarioImgs] = useState({});

  const API_URL = import.meta.env.VITE_API_URL;
  const currentUserId = parseInt(localStorage.getItem('archivault_user_id'), 10);
  const username = localStorage.getItem('archivault_user') || 'Usuario';

  const fetchData = useCallback(async () => {
    try {
      setSummaryError(false);
      const results = await Promise.allSettled([
        apiRequest(`${API_URL}/api/v1/community/posts/`),
        apiRequest(`${API_URL}/api/v1/accounts/users/`),
        apiRequest(`${API_URL}/api/v1/community/comentarios/`),
        apiRequest(`${API_URL}/api/v1/community/likes/`),
        loadCommunitySummary(API_URL),
        apiRequest(`${API_URL}/api/v1/accounts/profiles/`),
        apiRequest(`${API_URL}/api/v1/community/media/`)
      ]);
      if (results[0].status === 'rejected') throw results[0].reason;
      if (results[1].status === 'rejected') throw results[1].reason;
      const optionalData = index => {
        if (results[index].status === 'fulfilled') return results[index].value;
        logTechnicalError(results[index].reason, { view: 'community', secondaryRequest: index });
        return [];
      };
      const dataPosts = results[0].value;
      const dataUsers = results[1].value;
      const dataComentarios = optionalData(2);
      const dataLikes = optionalData(3);
      const dataSummary = optionalData(4);
      const dataProf = optionalData(5);
      const dataMedia = optionalData(6);
      if (results[4].status === 'rejected') setSummaryError(true);

      const postsArr = Array.isArray(dataPosts) ? dataPosts : dataPosts.results || [];
      const mediaArr = Array.isArray(dataMedia) ? dataMedia : dataMedia.results || [];
      const mediaMap = {};
      mediaArr.forEach(media => { if (!mediaMap[media.post]) mediaMap[media.post] = [media.archivo, media.url]; });
      setPosts(postsArr.map(post => ({ ...post, imagenes: mediaMap[post.id] || [] })));
      setComentarios(Array.isArray(dataComentarios) ? dataComentarios : dataComentarios.results || []);
      setLikes(Array.isArray(dataLikes) ? dataLikes : dataLikes.results || []);

      const map = {};
      const usersArray = Array.isArray(dataUsers) ? dataUsers : dataUsers.results || [];
      usersArray.forEach(u => { map[u.id] = u.username; });
      setUsersMap(map);

      const aMap = {};
      const profArray = Array.isArray(dataProf) ? dataProf : dataProf.results || [];
      profArray.forEach(p => { aMap[p.user] = p.avatar || null; });
      setAvatarsMap(aMap);

      const summary = normalizeCommunitySummary(dataSummary);
      setTopUsers(summary.coleccionistasTop);
      setNovedadesMkt(summary.novedadesMarketplace);

    } catch (error) { notifyApiError(addNotification, error, 'No se pudo cargar la comunidad'); } finally { setLoading(false); }
  }, [API_URL, addNotification]);

  useEffect(() => {
    // Data is updated asynchronously after the requests settle.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchData();
  }, [fetchData]);

  const handleImageUpload = (e) => {
      if(e.target.files && e.target.files[0]) {
          setImagenPost(e.target.files[0]);
          setImgPreview(URL.createObjectURL(e.target.files[0]));
      }
  };

  const handleComentarioImageUpload = (e, postId) => {
      if(e.target.files && e.target.files[0]) {
          setComentarioImgs({...comentarioImgs, [postId]: { file: e.target.files[0], preview: URL.createObjectURL(e.target.files[0]) }});
      }
  };

  const handlePublicar = async (e) => {
    e.preventDefault();
    if ((!nuevoContenido.trim() && !imagenPost) || isNaN(currentUserId)) return;
    setPublicando(true);

    const formData = new FormData();
    formData.append('user', currentUserId); 
    formData.append('contenido', nuevoContenido);

    try {
      const post = await apiRequest(`${API_URL}/api/v1/community/posts/`, { method: 'POST', body: formData });
        if (imagenPost) {
          const mediaForm = new FormData();
          mediaForm.append('post', post.id);
          mediaForm.append('archivo', imagenPost);
          mediaForm.append('tipo', imagenPost.type);
          await apiRequest(`${API_URL}/api/v1/community/media/`, { method: 'POST', body: mediaForm });
        }
        addNotification("Foro", "Publicación compartida exitosamente.", "success");
        setNuevoContenido(''); setImagenPost(null); setImgPreview(null); fetchData();
    } catch (error) { notifyApiError(addNotification, error, 'No se pudo crear la publicación'); } finally { setPublicando(false); }
  };

  const handleComentar = async (postId) => {
    const texto = comentariosTextos[postId];
    if (!texto || !texto.trim()) return;

    const formData = new FormData();
    formData.append('post', postId);
    formData.append('user', currentUserId);
    formData.append('contenido', texto || '');
    if (comentarioImgs[postId]?.file) formData.append('imagen', comentarioImgs[postId].file);

    try {
      await apiRequest(`${API_URL}/api/v1/community/comentarios/`, {
        method: 'POST', body: formData
      });
        addNotification("Foro", "Participaste en la discusión.", "info");
        setComentariosTextos({ ...comentariosTextos, [postId]: '' });
        setComentarioImgs({ ...comentarioImgs, [postId]: null });
        fetchData();
    } catch (error) { notifyApiError(addNotification, error, 'No se pudo enviar el comentario'); }
  };

  const handleLike = async (postId) => {
    if (isNaN(currentUserId)) return;
    const likeExistente = likes.find(l => l.post === postId && l.user === currentUserId);

    try {
      if (likeExistente) {
        await apiRequest(`${API_URL}/api/v1/community/likes/${likeExistente.id}/`, { method: 'DELETE' });
      } else {
        await apiRequest(`${API_URL}/api/v1/community/likes/`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ post: postId, user: currentUserId })
        });
      }
      fetchData(); 
    } catch (error) { notifyApiError(addNotification, error, 'No se pudo actualizar la reacción'); }
  };

  if (loading) return <div className="view-container community-state">Cargando Plaza Principal...</div>;

  return (
    <div className="view-container community-page">
      <div className="split-hero community-page__hero">
        <div className="hero-text community-page__hero-copy">
          <div className="eyebrow" style={{marginBottom: '16px', color: 'var(--vermilion)'}}>RED SOCIAL INTERACTIVA</div>
          <h1 className="h-1" style={{color: 'var(--paper)'}}>Foro ArchiVault</h1>
        </div>
      </div>

      <div className="layout-container layout-container--wide community-layout">
        <div className="community-feed">
          <div className="community-editor">
            <form onSubmit={handlePublicar}>
              <div className="community-editor__body">
                <div className="community-avatar community-avatar--editor" style={{background: 'var(--vermilion)'}}>
                  <MediaImage sources={avatarsMap[currentUserId]} alt={`Avatar de ${username}`} fallback={username.charAt(0).toUpperCase()} style={{width:'100%', height:'100%', objectFit:'cover'}} />
                </div>
                <div className="community-editor__content">
                  <textarea 
                    className="editorial-input" style={{padding: '8px 0', fontSize: '22px', resize: 'none', minHeight: '80px', borderBottom: 'none'}} 
                    placeholder="Comparte un descubrimiento con la comunidad..." 
                    value={nuevoContenido} onChange={(e) => setNuevoContenido(e.target.value)} required={!imgPreview}
                  />
                  {imgPreview && (
                      <div className="community-media-preview">
                          <MediaImage sources={imgPreview} alt="Vista previa" fallback={<Icons.Image />} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
                          <button type="button" className="community-media-remove" aria-label="Quitar imagen de la publicación" onClick={() => {setImgPreview(null); setImagenPost(null);}}><Icons.Close /></button>
                      </div>
                  )}
                  <div className="community-editor__actions">
                    <label className="community-file-action">
                        <Icons.Image /> Adjuntar Fotografía Real
                        <input type="file" style={{display: 'none'}} accept="image/*" aria-label="Adjuntar fotografía a la publicación" onChange={handleImageUpload} />
                    </label>
                    <button type="submit" className="btn btn--vermilion" disabled={publicando || (!nuevoContenido.trim() && !imgPreview)} style={{padding: '14px 40px', borderRadius: '999px'}}>
                      {publicando ? 'Publicando...' : 'Publicar'}
                    </button>
                  </div>
                </div>
              </div>
            </form>
          </div>

          {posts.map((post) => {
            const esMiPost = post.user === currentUserId;
            const nombreAutor = esMiPost ? `${username} (Tú)` : (usersMap[post.user] || "Coleccionista");
            const avatarUrl = avatarsMap[post.user];
            const postLikes = likes.filter(l => l.post === post.id);
            const aMiMeGusta = postLikes.some(l => l.user === currentUserId);
            const postComentarios = comentarios.filter(c => c.post === post.id);

            return (
              <article key={post.id} className="community-post">
                <div className="community-post__header">
                  <div className="community-avatar community-avatar--post" style={{background: esMiPost ? 'var(--vermilion)' : 'var(--sea)'}}>
                      <MediaImage sources={avatarUrl} alt={`Avatar de ${nombreAutor}`} fallback={nombreAutor.charAt(0).toUpperCase()} style={{width:'100%', height:'100%', objectFit:'cover'}} />
                  </div>
                  <div><div style={{fontFamily: 'var(--serif)', fontWeight: 'bold', fontSize:'20px', color: 'var(--ink)'}}>{nombreAutor}</div></div>
                </div>
                
                <div className="community-post__content">
                  <Link to={resourceRoutes.communityPost(post.id)} className="community-post__link"><p className="community-post__text">{post.contenido || ""}</p></Link>
                  {post.imagenes.length > 0 && (
                      <div className="community-post__media">
                          <MediaImage sources={post.imagenes} alt="Contenido adjunto" fallback={<Icons.Image />} style={{width: '100%', display: 'grid'}} />
                      </div>
                  )}
                </div>

                <div className="community-post__social">
                  <button type="button" className="community-social-action" onClick={() => handleLike(post.id)} style={{color: aMiMeGusta ? 'var(--vermilion)' : 'var(--ink-60)'}}>
                    <Icons.Heart filled={aMiMeGusta} /> 
                    {postLikes.length} Reacciones
                  </button>
                  <div className="community-social-action community-social-action--static">
                    <Icons.MessageCircle />
                    {postComentarios.length} Comentarios
                  </div>
                </div>

                <div className="community-post__comments">
                  {postComentarios.length > 0 && (
                    <div className="community-comments-list">
                      {postComentarios.map(comentario => (
                        <div key={comentario.id} className="community-comment">
                          <div className="community-avatar community-avatar--comment" style={{background: 'var(--ink)'}}>
                            <MediaImage sources={avatarsMap[comentario.user]} alt={`Avatar de ${usersMap[comentario.user] || 'usuario'}`} fallback={(usersMap[comentario.user] || "U").charAt(0).toUpperCase()} style={{width:'100%', height:'100%', objectFit:'cover'}} />
                          </div>
                          <div className="community-comment__bubble text-wrap-safe">
                            <strong style={{display: 'block', fontSize: '14px', fontFamily: 'var(--serif)', marginBottom: '8px', color: 'var(--sea)'}}>{usersMap[comentario.user] || "Coleccionista"}</strong>
                            <span style={{fontSize: '16px', color: 'var(--ink)', whiteSpace: 'pre-wrap'}}>{comentario.contenido || comentario.texto}</span>
                            {comentario.imagen && <MediaImage sources={comentario.imagen} alt="Imagen del comentario" fallback={<Icons.Image />} style={{width: '100%', marginTop: '12px', borderRadius: '8px'}} />}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  <div className="community-comment-composer">
                    {comentarioImgs[post.id]?.preview && (
                        <div className="community-comment-preview">
                            <MediaImage sources={comentarioImgs[post.id].preview} style={{width:'100%', height:'100%', objectFit:'cover'}} alt="Vista previa" fallback={<Icons.Image />} />
                            <button type="button" className="community-media-remove community-media-remove--compact" aria-label="Quitar imagen del comentario" onClick={() => setComentarioImgs({...comentarioImgs, [post.id]: null})}><Icons.Close /></button>
                        </div>
                    )}
                    <div className="community-comment-form">
                        <div className="community-avatar community-avatar--comment" style={{background: 'var(--vermilion)'}}>
                            <MediaImage sources={avatarsMap[currentUserId]} alt={`Avatar de ${username}`} fallback={username.charAt(0).toUpperCase()} style={{width:'100%', height:'100%', objectFit:'cover'}} />
                        </div>
                        <input 
                        type="text" className="editorial-input" 
                        style={{padding: '16px 24px', fontSize: '16px', borderRadius: '999px', background: 'var(--surface)', border: '1px solid var(--ink-20)'}}
                        placeholder="Añade a la discusión..."
                        value={comentariosTextos[post.id] || ''}
                        onChange={(e) => setComentariosTextos({...comentariosTextos, [post.id]: e.target.value})}
                        onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); handleComentar(post.id, post.user); } }}
                        />
                        <label className="community-comment-form__attachment touch-target" aria-label="Adjuntar imagen al comentario">
                            <Icons.Image />
                            <input type="file" style={{display:'none'}} accept="image/*" aria-label="Adjuntar imagen al comentario" onChange={(e) => handleComentarioImageUpload(e, post.id)} />
                        </label>
                        <button onClick={() => handleComentar(post.id, post.user)} className="btn btn--ink" style={{borderRadius: '999px', padding: '16px 32px'}} disabled={!comentariosTextos[post.id]?.trim() && !comentarioImgs[post.id]}>Responder</button>
                    </div>
                  </div>
                </div>
              </article>
            );
          })}
          {posts.length === 0 && <div className="community-state community-state--empty">Aún no hay publicaciones en la comunidad.</div>}
        </div>

        {/* SIDEBAR TENDENCIAS */}
        <aside className="community-sidebar">
          <div className="community-sidebar__panel">
              <div className="eyebrow" style={{marginBottom: '24px'}}>NOVEDADES EN MARKETPLACE</div>
              {summaryError ? (
                  <div style={{fontSize: '13px', color: 'var(--ink-60)'}}>No pudimos cargar las novedades en este momento.</div>
              ) : novedadesMkt.length === 0 ? (
                  <div style={{fontSize: '13px', color: 'var(--ink-60)'}}>No hay piezas recientes.</div>
              ) : (
                  <div className="community-insight-list">
                      {novedadesMkt.map(nov => (
                          <div key={nov.id} className="community-insight-item">
                              <strong style={{display: 'block', fontSize: '16px', fontFamily: 'var(--serif)'}}>{nov.nombre}</strong>
                              <span style={{display: 'block', color: 'var(--ink-60)', fontSize: '11px'}}>{nov.tipo === 'COLECCION' ? 'Colección' : 'Pieza'}</span>
                              <span style={{color: 'var(--vermilion)', fontWeight: 'bold', fontSize: '14px'}}>${nov.precio}</span>
                          </div>
                      ))}
                  </div>
              )}
          </div>
          <div className="community-sidebar__panel">
              <div className="eyebrow" style={{marginBottom: '24px'}}>COLECCIONISTAS TOP</div>
              <div className="community-insight-list">
                  {summaryError ? <div style={{fontSize: '13px', color: 'var(--ink-60)'}}>No pudimos cargar el ranking en este momento.</div> : topUsers.length === 0 ? <div style={{fontSize: '13px', color: 'var(--ink-60)'}}>Aún no hay interacciones suficientes.</div> : topUsers.map((user, i) => (
                      <div key={user.id} className="community-top-user">
                          <div style={{fontWeight: 'bold', color: 'var(--sea)'}}>#{i+1}</div>
                          <div style={{width: '32px', height: '32px', background: 'var(--ink)', color: 'var(--paper)', display: 'grid', placeItems: 'center', borderRadius: '50%', fontSize: '12px', fontWeight: 'bold', overflow:'hidden'}}>
                              <MediaImage sources={avatarsMap[user.id]} alt={`Avatar de ${user.nombre}`} fallback={user.nombre[0].toUpperCase()} style={{width:'100%', height:'100%', objectFit:'cover'}} />
                          </div>
                          <div><span style={{fontFamily: 'var(--serif)', fontWeight: 'bold', display: 'block'}}>{user.nombre}</span><small style={{color: 'var(--ink-60)'}}>{user.score} interacciones</small></div>
                      </div>
                  ))}
              </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
