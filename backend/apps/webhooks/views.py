from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError
from django.db import transaction

from .models import Notificacion, WebhookEvent
from .serializers import NotificacionSerializer
from apps.marketplace.models import Oferta
from apps.marketplace.services import complete_offer
from .security import verify_webhook_signature


class NotificacionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Notificacion.objects.all()
    serializer_class = NotificacionSerializer

    def get_queryset(self):
        return Notificacion.objects.filter(user=self.request.user).order_by("-fecha")

    @action(detail=False, methods=["post"], url_path="marcar-leidas")
    def mark_all_read(self, request):
        updated = self.get_queryset().filter(leido=False).update(leido=True)
        return Response({"actualizadas": updated}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="marcar-leida")
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        if not notification.leido:
            notification.leido = True
            notification.save(update_fields=["leido"])
        return Response(self.get_serializer(notification).data, status=status.HTTP_200_OK)


class WebhookReceiverView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        delivery_id = verify_webhook_signature(request)

        evento = request.data.get("evento")
        datos = request.data.get("datos", {})
        if evento != "pago_exitoso":
            raise ValidationError({"evento": "El evento indicado no está soportado."})

        oferta_id = datos.get("oferta_id")
        try:
            with transaction.atomic():
                event, _ = WebhookEvent.objects.get_or_create(
                    delivery_id=delivery_id,
                    defaults={"evento": evento},
                )
                event = WebhookEvent.objects.select_for_update().get(pk=event.pk)
                if event.procesado:
                    return Response(
                        {"mensaje": "Webhook procesado anteriormente", "duplicado": True},
                        status=status.HTTP_200_OK,
                    )

                oferta = Oferta.objects.select_related("publicacion__vendedor").get(id=oferta_id)
                complete_offer(oferta.id, oferta.publicacion.vendedor)
                event.procesado = True
                event.save(update_fields=["procesado"])
        except Oferta.DoesNotExist:
            raise NotFound() from None

        return Response({"mensaje": "Webhook procesado correctamente"}, status=status.HTTP_200_OK)
