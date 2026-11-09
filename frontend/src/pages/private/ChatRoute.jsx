import { useOutletContext } from 'react-router-dom';
import ResourceState from '../../components/ResourceState';

export default function ChatRoute() {
  const { chatRouteStatus } = useOutletContext();
  if (chatRouteStatus === 'loading' || chatRouteStatus === 'idle') return <ResourceState type="loading" />;
  if (chatRouteStatus === 'unavailable') return <ResourceState type="unavailable" backTo="/app/marketplace" backLabel="Volver al marketplace" />;
  if (chatRouteStatus === 'error') return <ResourceState type="error" backTo="/app/marketplace" backLabel="Volver al marketplace" />;
  return <div className="view-container" style={{ minHeight: '55vh', display: 'grid', placeItems: 'center', color: 'var(--ink-60)' }}>Conversación abierta</div>;
}
