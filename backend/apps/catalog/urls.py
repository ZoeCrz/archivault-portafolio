from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ColeccionMaestraViewSet,
    PiezaCatalogoViewSet,
    ColeccionUsuarioViewSet,
    PiezaInventarioViewSet,
    PiezaFotoViewSet,
    FavoritoViewSet,
)

router = DefaultRouter()
router.register(r"colecciones", ColeccionMaestraViewSet)
router.register(r"piezas-catalogo", PiezaCatalogoViewSet)
router.register(r"colecciones-usuario", ColeccionUsuarioViewSet)
router.register(r"inventario", PiezaInventarioViewSet)
router.register(r"fotos", PiezaFotoViewSet)
router.register(r"favoritos", FavoritoViewSet)

urlpatterns = [
    path("", include(router.urls)),
]