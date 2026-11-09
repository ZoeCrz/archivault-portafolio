# ArchiVault
Plataforma para organizar colecciones, publicar piezas, interactuar con otros coleccionistas y gestionar intercambios o ventas. Integra React, Django REST Framework, GraphQL y MySQL; conserva el diseño y los módulos del proyecto original.

## Características y resultados

- Catálogo de colecciones y piezas con imágenes y páginas de detalle.
- Comunidad con publicaciones, comentarios, favoritos, perfiles y notificaciones.
- Marketplace con publicaciones y búsqueda, integrado con las cuentas de usuario.
- API REST y GraphQL conectadas al frontend React. La demo puede cargar una colección ficticia para probar el flujo.
- Se integraron permisos, cambios de contraseña, validación de imágenes y pruebas de frontend y backend.

## Ejecutar en desarrollo
Requiere Docker con Compose v2.24 o posterior, Python 3.11+ para generar configuración y Node.js 24 con npm. Desde la raíz:
```sh
python3 backend/setup_local.py
cd backend
docker compose up --build
```
En otra terminal, desde la raíz:
```sh
cd frontend
npm ci
npm run dev
```
Abre http://localhost:5173. API en http://localhost:8000/api/v1/ y GraphQL en http://localhost:8000/graphql/. Registra tu cuenta desde la interfaz. Para cargar una colección y tres piezas ficticias, ejecuta `docker compose exec web python manage.py cargar_demo` desde `backend`. El comando se puede repetir en desarrollo. Para administrar Django:
```sh
cd backend
docker compose exec web python manage.py createsuperuser
```
`setup_local.py` crea secretos aleatorios en `backend/.env` y la URL del frontend en `frontend/.env`; no sobrescribe configuraciones existentes. No publiques estos archivos. Para detener: `docker compose down`; los datos persisten en volúmenes. Cambia el puerto 3306 del host si ya lo usa otra base local.

## Organización
- `backend/apps/`: cuentas, catálogo, comunidad, mercado y webhooks.
- `backend/config/`: configuración, permisos, GraphQL, almacenamiento y validadores.
- `frontend/src/`: páginas, componentes y servicios React.
- `.github/workflows/`: verificación y despliegue opcional.

## Pruebas
```sh
cd frontend
npm test
npm run build
# Desde backend, con Compose iniciado:
docker compose exec web python manage.py test --settings=config.test_settings
```
La verificación privada previa pasó el build de Vite y la suite de Django. Tras retirar los recursos sin uso se volvieron a ejecutar las 96 pruebas del frontend. El workflow de este repositorio vuelve a comprobar el build y ambas suites.

## Seguridad y configuración
Las peticiones autenticadas restringen los tokens al origen y rutas de API configurados. Las contraseñas se validan y se cambian por el endpoint `users/cambiar-password/` con `old_password` y `new_password`; no por un PATCH genérico al usuario. Los correos no se incluyen en representaciones de otros usuarios. Hay límites de peticiones y validación de imágenes decodificadas.

Django se actualizó a 5.2.19, DRF a 3.16.1 y se añadió Pillow 13.0.0. Estas son las versiones declaradas en el proyecto. Referencias de versiones: https://pypi.org/project/Django/5.2.19/ y https://pypi.org/project/Pillow/13.0.0/.

El despliegue AWS es manual y exige `ENABLE_DEPLOY=true` más las variables indicadas en el workflow; no incluye cuentas ni infraestructura del autor. La configuración Compose es para desarrollo local. Antes de desplegar: HTTPS, DEBUG=False, hosts/orígenes exactos, almacenamiento privado, copias de seguridad y revisión de dependencias. Los tokens siguen almacenándose en el navegador: una futura mejora es evaluar cookies HttpOnly y su protección CSRF.

## Alcance del portafolio
Proyecto de portafolio que integra catálogo, comunidad y publicaciones de marketplace. La guía cubre una instalación local. Un despliegue público requiere configurar el entorno y validar la seguridad de la instancia.
