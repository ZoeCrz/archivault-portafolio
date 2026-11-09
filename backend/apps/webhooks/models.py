from django.conf import settings
from django.db import models


class Notificacion(models.Model):
    EVENTOS = [
        ("POST_LIKE", "Reacción a publicación"),
        ("POST_COMMENT", "Comentario en publicación"),
        ("CHAT_MESSAGE", "Mensaje de chat"),
        ("OFFER_RECEIVED", "Oferta recibida"),
        ("OFFER_ACCEPTED", "Oferta aceptada"),
        ("OFFER_REJECTED", "Oferta rechazada"),
        ("SALE_COMPLETED_BUYER", "Compra completada"),
        ("SALE_COMPLETED_SELLER", "Venta completada"),
        ("GENERAL", "General"),
    ]
    DESTINOS = [
        ("COMMUNITY_POST", "Publicación de comunidad"),
        ("CHAT", "Chat"),
        ("MARKETPLACE_PUBLICATION", "Publicación de marketplace"),
    ]
    TIPOS = [
        ("oferta", "Oferta"),
        ("mensaje", "Mensaje"),
        ("venta", "Venta"),
        ("favorito", "Favorito"),
        ("comentario", "Comentario"),
        ("general", "General"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notificaciones"
    )
    tipo = models.CharField(max_length=20, choices=TIPOS)
    mensaje = models.TextField()
    evento = models.CharField(max_length=32, choices=EVENTOS, default="GENERAL")
    destino_tipo = models.CharField(
        max_length=32, choices=DESTINOS, null=True, blank=True
    )
    destino_id = models.PositiveBigIntegerField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    leido = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(destino_tipo__isnull=True, destino_id__isnull=True)
                    | models.Q(destino_tipo__isnull=False, destino_id__isnull=False)
                ),
                name="notification_destination_complete",
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.tipo}"


class WebhookEvent(models.Model):
    delivery_id = models.CharField(max_length=120, unique=True)
    evento = models.CharField(max_length=80)
    procesado = models.BooleanField(default=False)
    fecha_recepcion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.delivery_id} - {self.evento}"
