import { useState, useEffect, useCallback, useRef } from 'react';
import { Outlet, useNavigate, useMatch } from 'react-router-dom';
import { apiRequest, clearSession } from '../../services/api';
import { AppError, logTechnicalError, notifyApiError } from '../../services/errors';
import { resourceRoutes } from '../../services/routes';
import {
  loadPersistentNotifications,
  markAllNotificationsRead,
  markNotificationRead,
  notificationDestination,
} from '../../services/notifications';
import AppShell from '../navigation/AppShell.jsx';
import PrivateHeaderActions from '../navigation/PrivateHeaderActions.jsx';
import SiteFooter from '../navigation/SiteFooter.jsx';
import SiteHeader from '../navigation/SiteHeader.jsx';
import {
  PRIVATE_BRAND_PATH,
  PRIVATE_FOOTER_GROUPS,
  PRIVATE_NAVIGATION,
} from '../navigation/navigationConfig.js';

const Icons = {
  Close: () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>,
  Send: () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
};

function NotificationContent({ notification }) {
  return <>
    <div className="notification-popover__indicator" style={{background: notification.tipo === 'error' ? 'var(--negative)' : 'var(--sea)'}}></div>
    <div className="notification-popover__content text-wrap-safe">
      <div className="notification-popover__title">
        {notification.titulo}{!notification.leida && !notification.local ? ' · No leída' : ''}
      </div>
      <div className="notification-popover__message">{notification.mensaje}</div>
    </div>
  </>;
}

export default function PrivateLayout() {
  const navigate = useNavigate();
  const chatMatch = useMatch('/app/chats/:chatId');
  const API_URL = import.meta.env.VITE_API_URL;
  const userId = parseInt(localStorage.getItem('archivault_user_id'), 10);
  
  const [globalSearch, setGlobalSearch] = useState('');
  const [showNotifications, setShowNotifications] = useState(false);
  const [notificaciones, setNotificaciones] = useState([]);
  const [notificationCenterError, setNotificationCenterError] = useState('');
  
  const [chatState, setChatState] = useState({ open: false, chatId: null, userId: null, userName: '', messages: [] });
  const [chatRouteStatus, setChatRouteStatus] = useState('idle');
  const [msgInput, setMsgInput] = useState('');
  const lastMessageIdRef = useRef(0);
  const activeChatIdRef = useRef(null);
  const chatRequestInFlightRef = useRef(false);
  const messagesEndRef = useRef(null);

  const addNotification = useCallback((titulo, mensaje, tipo = 'info') => {
    const nuevaNotif = { id: `local-${Date.now()}`, titulo, mensaje, tipo, leida: false, local: true, fecha: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) };
    setNotificaciones(prev => [nuevaNotif, ...prev]);
  }, []);

  useEffect(() => {
      let active = true;
      const loadNotifications = async () => {
          try {
              const items = await loadPersistentNotifications(API_URL);
              if (active) {
                  const titles = { oferta: 'Actividad de Oferta', mensaje: 'Nuevo Mensaje', venta: 'Actividad de Venta', favorito: 'Nueva Reacción', comentario: 'Nuevo Comentario', general: 'Notificación' };
                  const persisted = items.map(item => ({
                      ...item,
                      titulo: titles[item.tipo] || 'Notificación',
                      fecha: new Date(item.fecha).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'}),
                  }));
                  setNotificaciones(prev => [...persisted, ...prev.filter(item => item.local)].slice(0, 30));
                  setNotificationCenterError('');
              }
          } catch(error) {
              logTechnicalError(error, { operation: 'load_notifications' });
              if (active) setNotificationCenterError('No pudimos actualizar las notificaciones en este momento.');
          }
      };
      
      loadNotifications();
      const interval = setInterval(loadNotifications, 10000);
      return () => { active = false; clearInterval(interval); };
  }, [userId, API_URL, navigate]);

  const handleNotificationToggle = () => {
      const opening = !showNotifications;
      setShowNotifications(opening);
      if (opening) {
          setNotificaciones(prev => prev.map(item => (
              item.local ? { ...item, leida: true } : item
          )));
      }
  };

  const handlePersistentNotification = async (notification) => {
      const destination = notificationDestination(notification);
      if (!notification.local && !notification.leida) {
          try {
              await markNotificationRead(API_URL, notification.id);
              setNotificaciones(prev => prev.map(item => (
                  item.id === notification.id ? { ...item, leida: true } : item
              )));
              setNotificationCenterError('');
          } catch (error) {
              logTechnicalError(error, { operation: 'mark_notification_read', notificationId: notification.id });
              setNotificationCenterError('No pudimos marcar la notificación como leída.');
          }
      }
      if (destination) {
          setShowNotifications(false);
          navigate(destination);
      }
  };

  const handleMarkAllNotificationsRead = async () => {
      try {
          await markAllNotificationsRead(API_URL);
          setNotificaciones(prev => prev.map(item => item.local ? item : { ...item, leida: true }));
          setNotificationCenterError('');
      } catch (error) {
          logTechnicalError(error, { operation: 'mark_all_notifications_read' });
          setNotificationCenterError('No pudimos marcar todas las notificaciones como leídas.');
      }
  };

  const fetchMessages = useCallback(async (chatId, incremental = false) => {
      if (!chatId || chatRequestInFlightRef.current) return;
      chatRequestInFlightRef.current = true;
      try {
          const after = incremental && lastMessageIdRef.current
              ? `&after=${lastMessageIdRef.current}`
              : '';
          const data = await apiRequest(`${API_URL}/api/v1/community/mensajes/?chat=${chatId}${after}`);
              const arr = Array.isArray(data) ? data : data.results || [];
              if (activeChatIdRef.current !== chatId) return;
              if (arr.length > 0) {
                  lastMessageIdRef.current = Math.max(
                      lastMessageIdRef.current,
                      ...arr.map(message => message.id),
                  );
              }
              setChatState(prev => {
                  if (prev.chatId !== chatId) return prev;
                  if (!incremental) return { ...prev, messages: arr };
                  const knownIds = new Set(prev.messages.map(message => message.id));
                  return {
                      ...prev,
                      messages: [...prev.messages, ...arr.filter(message => !knownIds.has(message.id))],
                  };
              });
      } catch (error) { logTechnicalError(error, { operation: 'poll_chat_messages' }); } finally { chatRequestInFlightRef.current = false; }
  }, [API_URL]);

  useEffect(() => {
      const rawChatId = chatMatch?.params.chatId;
      if (!rawChatId) {
          activeChatIdRef.current = null;
          // Route changes are the external event synchronized by this effect.
          // eslint-disable-next-line react-hooks/set-state-in-effect
          setChatState(prev => prev.open ? { ...prev, open: false } : prev);
          setChatRouteStatus('idle');
          return;
      }
      const chatId = Number.parseInt(rawChatId, 10);
      if (!Number.isInteger(chatId)) {
          setChatRouteStatus('unavailable');
          return;
      }
      let active = true;
      setChatRouteStatus('loading');
      const openRouteChat = async () => {
          try {
              const chat = await apiRequest(`${API_URL}/api/v1/community/chats/${chatId}/`);
              const targetUserId = chat.usuarios.find(id => id !== userId) || userId;
              const targetUser = await apiRequest(`${API_URL}/api/v1/accounts/users/${targetUserId}/`);
              if (!active) return;
              lastMessageIdRef.current = 0;
              activeChatIdRef.current = chatId;
              setChatState({ open: true, chatId, userId: targetUserId, userName: targetUser.username, messages: [] });
              setChatRouteStatus('ready');
              fetchMessages(chatId);
          } catch (error) {
              if (!active) return;
              setChatState(prev => ({ ...prev, open: false }));
              setChatRouteStatus(error instanceof AppError && ['not_found', 'permission_denied'].includes(error.code) ? 'unavailable' : 'error');
          }
      };
      openRouteChat();
      return () => { active = false; };
  }, [API_URL, chatMatch?.params.chatId, fetchMessages, userId]);

  useEffect(() => {
      if (!chatState.open || !chatState.chatId) return undefined;
      const pollMessages = () => {
          if (document.visibilityState === 'visible') {
              fetchMessages(chatState.chatId, true);
          }
      };
      const interval = setInterval(pollMessages, 3000);
      document.addEventListener('visibilitychange', pollMessages);
      return () => {
          clearInterval(interval);
          document.removeEventListener('visibilitychange', pollMessages);
      };
  }, [chatState.open, chatState.chatId, fetchMessages]);

  useEffect(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatState.messages.length]);

  const openChatWithUser = async (targetUserId, targetUserName) => {
      lastMessageIdRef.current = 0;
      activeChatIdRef.current = null;
      setChatState({ open: true, chatId: null, userId: targetUserId, userName: targetUserName, messages: [] });
      try {
          const dataChats = await apiRequest(`${API_URL}/api/v1/community/chats/`);
              const arrChats = Array.isArray(dataChats) ? dataChats : dataChats.results || [];
              const chatExistente = arrChats.find(c =>
                  Array.isArray(c.usuarios) &&
                  c.usuarios.includes(userId) &&
                  c.usuarios.includes(targetUserId)
              );

              if (chatExistente) {
                  navigate(resourceRoutes.chat(chatExistente.id));
              } else {
                  const newChat = await apiRequest(`${API_URL}/api/v1/community/chats/`, {
                      method: 'POST', headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ usuarios: [userId, targetUserId] })
                  });
                      navigate(resourceRoutes.chat(newChat.id));
              }
      } catch (error) { notifyApiError(addNotification, error, 'No se pudo abrir el chat'); }
  };

  const handleSendMessage = async () => {
      if(!msgInput.trim() || !chatState.chatId) return;
      try {
          const message = await apiRequest(`${API_URL}/api/v1/community/mensajes/`, {
              method: 'POST', headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ chat: chatState.chatId, user: userId, contenido: msgInput })
          });
              setMsgInput('');
              lastMessageIdRef.current = Math.max(lastMessageIdRef.current, message.id);
              setChatState(prev => {
                  if (prev.chatId !== chatState.chatId || prev.messages.some(item => item.id === message.id)) return prev;
                  return { ...prev, messages: [...prev.messages, message] };
              });
      } catch (error) { notifyApiError(addNotification, error, 'No se pudo enviar el mensaje'); }
  };

  const handleSearchSubmit = (e) => {
    if (e.key === 'Enter' && globalSearch.trim()) {
      navigate(`/app/marketplace?q=${encodeURIComponent(globalSearch.trim())}`);
      setGlobalSearch('');
    }
  };

  const handleLogout = () => {
    clearSession();
    navigate('/login');
  };

  const unreadCount = notificaciones.filter(n => !n.leida).length;

  const notificationPanel = showNotifications ? (
    <div className="notification-popover" role="region" aria-label="Centro de notificaciones">
      <div className="eyebrow notification-popover__header">CENTRO DE NOTIFICACIONES</div>
      {notificaciones.some(item => !item.local && !item.leida) && (
        <button type="button" onClick={handleMarkAllNotificationsRead} className="btn btn--outline btn--sm" style={{margin: '12px 20px 4px'}}>
          Marcar todas como leídas
        </button>
      )}
      {notificationCenterError && <div role="status" className="notification-popover__error">{notificationCenterError}</div>}
      <div className="notification-popover__list">
        {notificaciones.length === 0 ? <div className="notification-popover__empty">No hay actividad reciente.</div> : notificaciones.map(notif => (
          notificationDestination(notif) ? (
            <button
              type="button"
              key={notif.id}
              onClick={() => handlePersistentNotification(notif)}
              aria-label={`${notif.titulo}. ${notif.mensaje}${notif.leida ? '' : '. No leída'}`}
              className="notification-popover__item"
              style={{background: notif.leida ? 'transparent' : 'var(--surface)'}}
            >
              <NotificationContent notification={notif} />
            </button>
          ) : (
            <div key={notif.id} className="notification-popover__item notification-popover__item--static">
              <NotificationContent notification={notif} />
              {!notif.local && !notif.leida && <button type="button" className="btn btn--outline btn--sm" onClick={() => handlePersistentNotification(notif)}>Marcar como leída</button>}
            </div>
          )
        ))}
      </div>
    </div>
  ) : null;

  return (
    <>
      <AppShell
        header={(
          <SiteHeader
            brandTo={PRIVATE_BRAND_PATH}
            navigationItems={PRIVATE_NAVIGATION}
            actions={(
              <PrivateHeaderActions
                searchValue={globalSearch}
                onSearchChange={event => setGlobalSearch(event.target.value)}
                onSearchKeyDown={handleSearchSubmit}
                notificationsOpen={showNotifications}
                onNotificationsToggle={handleNotificationToggle}
                unreadCount={unreadCount}
                notificationPanel={notificationPanel}
                onLogout={handleLogout}
              />
            )}
          />
        )}
        footer={<SiteFooter brandTo={PRIVATE_BRAND_PATH} groups={PRIVATE_FOOTER_GROUPS} />}
      >
        <Outlet context={{ addNotification, openChatWithUser, chatRouteStatus }} />
      </AppShell>

      {chatState.open && (
        <div className="chat-popover" role="dialog" aria-label={`Chat con ${chatState.userName}`}>
            <div className="chat-popover__header">
                <div style={{display: 'flex', alignItems: 'center', gap: '8px'}}>
                    <div style={{width: '8px', height: '8px', background: '#4CAF50', borderRadius: '50%'}}></div>
                    <span style={{fontFamily: 'var(--serif)', fontWeight: 'bold', fontSize: '16px'}}>{chatState.userName}</span>
                </div>
                <button type="button" className="chat-popover__icon-button" aria-label="Cerrar chat" onClick={() => navigate('/app/marketplace')}><Icons.Close /></button>
            </div>
            <div className="chat-popover__messages">
                {chatState.messages.map(m => (
                    <div key={m.id} style={{maxWidth: '85%', padding: '10px 14px', borderRadius: '12px', fontSize: '13px', lineHeight: '1.4', wordWrap: 'break-word', alignSelf: m.user === userId ? 'flex-end' : 'flex-start', background: m.user === userId ? 'var(--sea)' : 'var(--paper)', color: m.user === userId ? 'var(--paper)' : 'var(--ink)', border: m.user === userId ? 'none' : '1px solid var(--ink-10)'}}>
                        {m.contenido}
                    </div>
                ))}
                <div ref={messagesEndRef}></div>
            </div>
            <div className="chat-popover__composer">
                <input type="text" className="chat-popover__input" placeholder="Escribe un mensaje..." value={msgInput} onChange={e => setMsgInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleSendMessage()}/>
                <button type="button" className="chat-popover__send" aria-label="Enviar mensaje" onClick={handleSendMessage}><Icons.Send /></button>
            </div>
        </div>
      )}
    </>
  );
}
