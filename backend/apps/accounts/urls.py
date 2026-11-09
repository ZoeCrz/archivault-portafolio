from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import UserViewSet, ProfileViewSet, MetodoPagoViewSet, ResenaViewSet, login_view

router = DefaultRouter()
router.register(r"users", UserViewSet)
router.register(r"profiles", ProfileViewSet)
router.register(r"metodos-pago", MetodoPagoViewSet)
router.register(r"resenas", ResenaViewSet)

urlpatterns = [
    # IMPORTANTE: Esta ruta personalizada debe ir antes del router
    path("login/", login_view, name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("", include(router.urls)),
]
