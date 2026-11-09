export const PROVISIONAL_LEGAL_NOTICE = 'Documento provisional para una aplicación de demostración. Antes de utilizar ArchiVault en producción, este contenido debe revisarse y completarse con información jurídica y organizativa real.';

export const PUBLIC_INFORMATION_PATHS = {
  help: '/ayuda',
  privacy: '/privacidad',
  terms: '/terminos',
  contact: '/contacto',
};

export const helpContent = {
  path: PUBLIC_INFORMATION_PATHS.help,
  title: 'Ayuda y preguntas frecuentes',
  introduction: 'Consulta cómo utilizar las funciones disponibles actualmente en ArchiVault y qué hacer ante los problemas más habituales.',
  sections: [
    {
      id: 'primeros-pasos',
      title: 'Primeros pasos',
      paragraphs: ['Crea una cuenta, inicia sesión y entra en Mis Colecciones para comenzar a organizar tu inventario. Desde Nueva Pieza puedes registrar una pieza, sus datos y fotografías.'],
      bullets: [
        'Utiliza un nombre de usuario, correo y contraseña válidos al crear la cuenta.',
        'Mis Colecciones reúne las colecciones en las que participas.',
        'Nueva Pieza permite registrar una pieza dentro de una colección y, opcionalmente, publicarla en el marketplace.',
      ],
    },
    {
      id: 'colecciones',
      title: 'Colecciones',
      paragraphs: ['Una colección general describe el conjunto compartido de piezas. Tu colección representa tu participación personal en ese conjunto y contiene tu progreso e inventario. También puedes crear colecciones propias.'],
      bullets: [
        'Las colecciones globales pueden ser utilizadas por varios coleccionistas.',
        'Las colecciones personales pertenecen a su creador y su acceso depende de las reglas de visibilidad.',
        'Una pieza puede configurarse como pública o privada. El backend vuelve a comprobar los permisos al abrir cada recurso.',
      ],
    },
    {
      id: 'marketplace',
      title: 'Marketplace',
      paragraphs: ['Puedes publicar piezas o colecciones indicando precio, condición y una descripción breve. Otros usuarios pueden realizar ofertas y el vendedor puede aceptarlas, rechazarlas o completar la venta.'],
      bullets: [
        'La condición disponible es Nueva, Usada o Dañada.',
        'Los estados de oferta y venta se gestionan dentro de la aplicación.',
        'ArchiVault no actúa actualmente como procesador de pagos, custodio financiero, garante de autenticidad, servicio de envíos ni mediador de disputas.',
      ],
    },
    {
      id: 'favoritos',
      title: 'Favoritos',
      paragraphs: ['Puedes marcar como favoritas piezas de inventario y colecciones generales. El filtro “Sólo favoritos” del marketplace permite localizar publicaciones asociadas a esos recursos.'],
    },
    {
      id: 'comunidad',
      title: 'Comunidad y chat',
      paragraphs: ['La comunidad permite compartir publicaciones y multimedia, reaccionar, comentar y consultar novedades. Los chats permiten conversar con otros usuarios mediante mensajes que la interfaz actualiza periódicamente.'],
    },
    {
      id: 'notificaciones',
      title: 'Notificaciones',
      paragraphs: ['Las notificaciones persistentes pueden abrir el post, chat o publicación de marketplace relacionado. Puedes marcarlas individualmente o utilizar “Marcar todas como leídas”.'],
      bullets: ['Si el recurso fue eliminado, se volvió privado o dejó de estar disponible, la aplicación mostrará un estado amigable sin revelar información restringida.'],
    },
    {
      id: 'problemas-frecuentes',
      title: 'Problemas frecuentes',
      subsections: [
        { title: 'Una imagen no aparece', paragraphs: ['Recarga la página y comprueba la conexión. Si el archivo ya no está disponible, la interfaz mostrará una imagen alternativa.'] },
        { title: 'La sesión expiró', paragraphs: ['Inicia sesión nuevamente. Si abriste un enlace privado, la aplicación intentará devolverte a ese recurso después del login.'] },
        { title: 'El contenido no está disponible', paragraphs: ['Puede haber sido eliminado, haberse vuelto privado o no pertenecer a tu cuenta. La aplicación no distingue públicamente esos casos para proteger la privacidad.'] },
        { title: 'Error de red', paragraphs: ['Comprueba tu conexión e inténtalo nuevamente.'] },
        { title: 'Error interno', paragraphs: ['Intenta la operación de nuevo. Si aparece un identificador de solicitud, consérvalo para facilitar un diagnóstico posterior.'] },
      ],
    },
    {
      id: 'obtener-ayuda',
      title: 'Contacto',
      paragraphs: ['Esta versión demostrativa todavía no dispone de un canal operativo de soporte. La página de contacto explica el estado actual y la información pendiente antes de producción.'],
      links: [{ label: 'Consultar la página de contacto', to: PUBLIC_INFORMATION_PATHS.contact }],
    },
  ],
};

export const privacyContent = {
  path: PUBLIC_INFORMATION_PATHS.privacy,
  title: 'Política de Privacidad',
  introduction: 'Resumen provisional de los datos y comportamientos actualmente verificables en ArchiVault.',
  version: 'Versión demostrativa — agosto de 2026',
  notice: PROVISIONAL_LEGAL_NOTICE,
  sections: [
    {
      id: 'datos-cuenta',
      title: 'Datos de cuenta y sesión',
      paragraphs: ['La aplicación registra el nombre de usuario y el correo proporcionado durante la creación de la cuenta. Las credenciales son gestionadas por el sistema de autenticación de Django.'],
      bullets: ['El frontend utiliza tokens de acceso y renovación para mantener la sesión.', 'Estos tokens se almacenan actualmente en el almacenamiento local del navegador.'],
    },
    {
      id: 'perfil',
      title: 'Perfil',
      paragraphs: ['El perfil puede contener avatar, ubicación, preferencia de visibilidad, reputación y reseñas asociadas a la cuenta.'],
    },
    {
      id: 'contenido',
      title: 'Colecciones, comunidad y mensajes',
      bullets: ['Colecciones, piezas, fotografías y progreso.', 'Publicaciones de comunidad, multimedia, comentarios y likes.', 'Chats y mensajes entre sus participantes.'],
    },
    {
      id: 'marketplace',
      title: 'Marketplace',
      paragraphs: ['Las publicaciones almacenan producto, precio, condición, descripción, vendedor, ofertas y estado de venta.'],
      bullets: ['Si el usuario registra un método de pago, el modelo actual puede almacenar la plataforma, un alias, un correo de pago y si está activo.', 'Esta descripción no implica que ArchiVault procese o custodie pagos.'],
    },
    {
      id: 'finalidades',
      title: 'Finalidades funcionales',
      bullets: ['Operar la cuenta y autenticar la sesión.', 'Mostrar contenido según propiedad, participación y visibilidad.', 'Permitir inventario, marketplace, comunidad, chat y notificaciones.', 'Mantener la integridad y seguridad funcional de las operaciones.'],
    },
    {
      id: 'multimedia',
      title: 'Archivos multimedia',
      paragraphs: ['En desarrollo, los archivos se almacenan mediante el filesystem local configurado por Django. El código dispone de soporte opcional para un almacenamiento S3 privado cuando se active y configure expresamente. No se ha verificado desde este repositorio que dicho almacenamiento esté activo en producción.'],
    },
    {
      id: 'pendientes-legales',
      title: 'Información pendiente antes de producción',
      notice: 'Esta sección requiere definición organizativa y revisión legal antes de publicar el servicio.',
      bullets: ['Responsable u operador del servicio.', 'Domicilio y contacto formal de privacidad.', 'Bases jurídicas y plazos de conservación.', 'Proveedores o encargados del tratamiento.', 'Transferencias internacionales.', 'Procedimiento para ejercer derechos del usuario.', 'Cookies o analítica, si se incorporan.', 'Legislación y autoridad competente.', 'Tratamiento de menores.', 'Protocolo de respuesta ante incidentes.'],
    },
  ],
};

export const termsContent = {
  path: PUBLIC_INFORMATION_PATHS.terms,
  title: 'Términos y Condiciones',
  introduction: 'Descripción provisional de reglas de uso coherentes con la versión demostrativa de ArchiVault.',
  version: 'Versión demostrativa — agosto de 2026',
  notice: PROVISIONAL_LEGAL_NOTICE,
  sections: [
    { id: 'naturaleza', title: 'Naturaleza de demostración', paragraphs: ['ArchiVault es actualmente un proyecto demostrativo y no debe presentarse como un servicio comercial plenamente operativo. Sus funciones pueden cambiar o experimentar interrupciones.'] },
    { id: 'cuentas', title: 'Cuentas', bullets: ['Cada usuario es responsable de proteger sus credenciales.', 'No se permite utilizar la aplicación para suplantar a otra persona, acceder sin autorización o realizar un uso abusivo.'] },
    { id: 'contenido', title: 'Contenido del usuario', paragraphs: ['El usuario es responsable del contenido que registra o publica y no debe incorporar material ilegal o que vulnere derechos de terceros.'], bullets: ['La aplicación necesita almacenar y mostrar técnicamente el contenido de acuerdo con la visibilidad seleccionada.', 'La licencia y las condiciones definitivas sobre contenido requieren revisión antes de producción.'] },
    { id: 'comunidad', title: 'Comunidad', bullets: ['Mantén una conducta respetuosa.', 'No publiques spam, fraude, acoso ni contenido malicioso.', 'La versión actual no afirma disponer de un equipo formal de moderación. Las políticas y procedimientos de moderación deben definirse antes de producción.'] },
    { id: 'marketplace', title: 'Marketplace', paragraphs: ['Los anuncios y sus datos son proporcionados por los vendedores. La condición, descripción y precio deben reflejar honestamente el producto ofrecido.'], bullets: ['Las ofertas utilizan estados internos de la aplicación.', 'ArchiVault no garantiza actualmente pagos, autenticidad, envíos, devoluciones ni resolución de disputas.'] },
    { id: 'disponibilidad', title: 'Disponibilidad', paragraphs: ['La demostración puede contener errores, cambios e interrupciones. No constituye una garantía contractual de disponibilidad o conservación permanente.'] },
    { id: 'propiedad-intelectual', title: 'Propiedad intelectual', paragraphs: ['Los derechos sobre software, marca y contenido deben corresponder a sus titulares legítimos. La definición de licencias, autorizaciones y titularidad aplicables queda pendiente de revisión.'] },
    { id: 'suspension', title: 'Suspensión y cierre', paragraphs: ['Las causas, el procedimiento y los efectos de suspender cuentas o cerrar el servicio no están definidos como política definitiva y deben establecerse antes de producción.'] },
    { id: 'pendientes-legales', title: 'Condiciones pendientes antes de producción', notice: 'Los siguientes puntos no están definidos y requieren decisión organizativa y revisión legal.', bullets: ['Operador del servicio y edad mínima.', 'Formación contractual y límites de responsabilidad.', 'Legislación y jurisdicción aplicables.', 'Propiedad intelectual definitiva.', 'Cancelaciones, devoluciones y disputas.', 'Impuestos y normativa de consumo.', 'Procedimiento de retirada de contenido.', 'Pagos, posibles comisiones y responsabilidades asociadas.'] },
  ],
};

export const contactContent = {
  path: PUBLIC_INFORMATION_PATHS.contact,
  title: 'Contacto',
  introduction: 'Información sobre el estado actual del soporte de ArchiVault.',
  notice: 'Esta versión de demostración todavía no dispone de un canal operativo de soporte. Antes de su publicación deberá incorporarse información de contacto real y verificada.',
  sections: [
    { id: 'ayuda-disponible', title: 'Ayuda disponible', paragraphs: ['Consulta primero las preguntas frecuentes y las recomendaciones para problemas habituales.'], links: [{ label: 'Ir a Ayuda y FAQ', to: PUBLIC_INFORMATION_PATHS.help }] },
    { id: 'identificador-solicitud', title: 'Identificador de solicitud', paragraphs: ['Si un error muestra un request_id, consérvalo. Ese identificador puede facilitar el diagnóstico cuando exista un canal de soporte, pero no contiene por sí mismo una solución ni garantiza una respuesta.'] },
    { id: 'pendientes-produccion', title: 'Información pendiente para producción', bullets: ['Correo de soporte verificado.', 'Responsable del canal.', 'Horario de atención.', 'Procedimiento formal para solicitudes de privacidad.'] },
  ],
};

export const PUBLIC_INFORMATION_PAGES = [helpContent, privacyContent, termsContent, contactContent];
