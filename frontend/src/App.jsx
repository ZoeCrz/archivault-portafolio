import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

// Layouts
import PublicLayout from './components/layouts/PublicLayout';
import PrivateLayout from './components/layouts/PrivateLayout';
import RequireAuth from './components/RequireAuth';

// Páginas Públicas
import Landing from './pages/public/Landing';
import Login from './pages/public/Login';
import CrearCuenta from './pages/public/CrearCuenta';
import Ayuda from './pages/public/Ayuda';
import Privacidad from './pages/public/Privacidad';
import Terminos from './pages/public/Terminos';
import Contacto from './pages/public/Contacto';
import NotFound from './pages/public/NotFound';

import MisColecciones from './pages/private/MisColecciones';
import NuevaPieza from './pages/private/NuevaPieza';
import DetalleColeccion from './pages/private/DetalleColeccion';
import Marketplace from './pages/private/Marketplace';
import Comunidad from './pages/private/Comunidad';
import Perfil from './pages/private/Perfil';
import DetalleMarketplace from './pages/private/DetalleMarketplace';
import DetallePost from './pages/private/DetallePost';
import PerfilPublico from './pages/private/PerfilPublico';
import ChatRoute from './pages/private/ChatRoute';

export default function App() {
  // Eliminamos la simulación global. Ahora delegamos la responsabilidad a cada página.
  return (
    <BrowserRouter>
      <Routes>
        
        {/* --- RUTAS PÚBLICAS --- */}
        <Route element={<PublicLayout />}>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/crear-cuenta" element={<CrearCuenta />} />
          <Route path="/ayuda" element={<Ayuda />} />
          <Route path="/privacidad" element={<Privacidad />} />
          <Route path="/terminos" element={<Terminos />} />
          <Route path="/contacto" element={<Contacto />} />
          <Route path="*" element={<NotFound />} />
        </Route>

        {/* --- RUTAS PRIVADAS --- */}
        <Route element={<RequireAuth />}>
          <Route path="/app" element={<PrivateLayout />}>
            {/* Redirigir /app a /app/colecciones por defecto */}
            <Route index element={<Navigate to="colecciones" replace />} />

            {/* Componentes independientes sin pasar props falsas */}
            <Route path="colecciones" element={<MisColecciones />} />
            <Route path="colecciones/:coleccionUsuarioId" element={<DetalleColeccion />} />
            <Route path="nueva-pieza" element={<NuevaPieza />} />
            <Route path="coleccion-detalle" element={<Navigate to="/app/colecciones" replace />} />
            <Route path="marketplace" element={<Marketplace />} />
            <Route path="marketplace/publicaciones/:publicacionId" element={<DetalleMarketplace />} />
            <Route path="comunidad" element={<Comunidad />} />
            <Route path="comunidad/publicaciones/:postId" element={<DetallePost />} />
            <Route path="perfil" element={<Perfil />} />
            <Route path="perfiles/:profileId" element={<PerfilPublico />} />
            <Route path="chats/:chatId" element={<ChatRoute />} />
          </Route>
        </Route>

      </Routes>
    </BrowserRouter>
  );
}
