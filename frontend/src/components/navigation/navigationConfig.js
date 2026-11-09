export const PUBLIC_BRAND_PATH = '/';
export const PRIVATE_BRAND_PATH = '/app/colecciones';

export const PUBLIC_NAVIGATION = [
  { label: 'Inicio', to: '/', exact: true },
];

export const PRIVATE_NAVIGATION = [
  { label: 'Mis Colecciones', to: '/app/colecciones' },
  { label: 'Marketplace', to: '/app/marketplace' },
  { label: 'Comunidad', to: '/app/comunidad' },
  { label: '+ Nueva Pieza', to: '/app/nueva-pieza', exact: true, accent: true },
];

export const INFORMATION_FOOTER_GROUP = {
  title: 'Información',
  links: [
    { label: 'Ayuda y FAQ', to: '/ayuda' },
    { label: 'Política de Privacidad', to: '/privacidad' },
    { label: 'Términos y Condiciones', to: '/terminos' },
    { label: 'Contacto', to: '/contacto' },
  ],
};

export const PUBLIC_FOOTER_GROUPS = [
  {
    title: 'Navegación',
    links: [
      { label: 'Inicio', to: '/' },
      { label: 'Iniciar sesión', to: '/login' },
      { label: 'Crear cuenta', to: '/crear-cuenta' },
    ],
  },
  INFORMATION_FOOTER_GROUP,
];

export const AUTHENTICATED_PUBLIC_FOOTER_GROUPS = [
  {
    title: 'Navegación',
    links: [
      { label: 'Inicio', to: '/' },
      { label: 'Volver a mi bóveda', to: '/app/colecciones' },
    ],
  },
  INFORMATION_FOOTER_GROUP,
];

export const PRIVATE_FOOTER_GROUPS = [
  {
    title: 'Colecciones',
    links: [
      { label: 'Mis Colecciones', to: '/app/colecciones' },
      { label: 'Nueva Pieza', to: '/app/nueva-pieza' },
    ],
  },
  {
    title: 'Explorar',
    links: [
      { label: 'Marketplace', to: '/app/marketplace' },
      { label: 'Comunidad', to: '/app/comunidad' },
    ],
  },
  {
    title: 'Cuenta',
    links: [
      { label: 'Mi Perfil', to: '/app/perfil' },
    ],
  },
  INFORMATION_FOOTER_GROUP,
];

export function isNavigationItemActive(item, pathname) {
  if (!item?.to || typeof pathname !== 'string') return false;
  if (item.exact) return pathname === item.to;
  return pathname === item.to || pathname.startsWith(`${item.to}/`);
}
