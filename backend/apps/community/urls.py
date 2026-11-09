from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PostViewSet,
    PostMediaViewSet,
    PostLikeViewSet,
    ComentarioViewSet,
    ChatViewSet,
    MensajeViewSet,
    CommunitySummaryView,
)

router = DefaultRouter()
router.register(r"posts", PostViewSet)
router.register(r"media", PostMediaViewSet)
router.register(r"likes", PostLikeViewSet)
router.register(r"comentarios", ComentarioViewSet)
router.register(r"chats", ChatViewSet)
router.register(r"mensajes", MensajeViewSet)

urlpatterns = [
    path("resumen/", CommunitySummaryView.as_view(), name="community-summary"),
    path("", include(router.urls)),
]
