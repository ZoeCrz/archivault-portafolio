from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import NotificacionViewSet, WebhookReceiverView

router = DefaultRouter()
router.register(r"notificaciones", NotificacionViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("receive/", WebhookReceiverView.as_view()),
]