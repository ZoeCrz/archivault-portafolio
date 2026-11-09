from rest_framework import serializers
from .models import Notificacion

class NotificacionSerializer(serializers.ModelSerializer):
    destino = serializers.SerializerMethodField()

    DESTINATION_ROUTES = {
        "COMMUNITY_POST": "/app/comunidad/publicaciones/{id}",
        "CHAT": "/app/chats/{id}",
        "MARKETPLACE_PUBLICATION": "/app/marketplace/publicaciones/{id}",
    }

    def get_destino(self, obj):
        route = self.DESTINATION_ROUTES.get(obj.destino_tipo)
        if not route or obj.destino_id is None:
            return None
        return {
            "tipo": obj.destino_tipo,
            "id": obj.destino_id,
            "url": route.format(id=obj.destino_id),
        }

    class Meta:
        model = Notificacion
        fields = ["id", "tipo", "evento", "mensaje", "leido", "fecha", "destino"]
        read_only_fields = fields
