from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PublicacionMarketViewSet, OfertaViewSet

router = DefaultRouter()
router.register(r"publicaciones", PublicacionMarketViewSet)
router.register(r"ofertas", OfertaViewSet)

urlpatterns = [
    path("", include(router.urls)),
]