from rest_framework import serializers
from .models import Post, PostMedia, PostLike, Comentario, Chat, Mensaje
from apps.webhooks.notifications import notify
from config.serializer_fields import MediaFileField


class MarketplaceNewsSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    tipo = serializers.CharField(source="insight_tipo", read_only=True)
    nombre = serializers.CharField(source="insight_nombre", read_only=True)
    precio = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    fecha_publicacion = serializers.DateTimeField(read_only=True)


class TopCollectorSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    nombre = serializers.CharField(source="username", read_only=True)
    likes_recibidos = serializers.IntegerField(read_only=True)
    comentarios_recibidos = serializers.IntegerField(read_only=True)
    score = serializers.IntegerField(read_only=True)


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = "__all__"
        read_only_fields = ["user"]


class PostMediaSerializer(serializers.ModelSerializer):
    archivo = MediaFileField(required=False, allow_null=True)

    def validate(self, attrs):
        url = attrs.get("url", getattr(self.instance, "url", ""))
        archivo = attrs.get("archivo", getattr(self.instance, "archivo", None))
        if not url and not archivo:
            raise serializers.ValidationError("Debes proporcionar un archivo o una URL.")
        return attrs

    def validate_post(self, post):
        if post.user_id != self.context["request"].user.id:
            raise serializers.ValidationError("No puedes adjuntar contenido a un post ajeno.")
        return post

    class Meta:
        model = PostMedia
        fields = "__all__"


class PostLikeSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        user = self.context["request"].user
        post = attrs.get("post", getattr(self.instance, "post", None))
        duplicate = PostLike.objects.filter(user=user, post=post)
        if self.instance:
            duplicate = duplicate.exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise serializers.ValidationError("Ya reaccionaste a esta publicación.")
        return attrs

    def create(self, validated_data):
        like = super().create(validated_data)
        if like.post.user_id != like.user_id:
            notify(
                like.post.user,
                "favorito",
                f"{like.user.username} reaccionó a tu publicación.",
                evento="POST_LIKE",
                destino_tipo="COMMUNITY_POST",
                destino_id=like.post_id,
                metadata={
                    "actor_id": like.user_id,
                    "actor_name": like.user.username,
                },
            )
        return like

    class Meta:
        model = PostLike
        fields = "__all__"
        read_only_fields = ["user"]


class ComentarioSerializer(serializers.ModelSerializer):
    imagen = MediaFileField(required=False, allow_null=True)

    def create(self, validated_data):
        comment = super().create(validated_data)
        if comment.post.user_id != comment.user_id:
            notify(
                comment.post.user,
                "comentario",
                f"{comment.user.username} comentó tu publicación.",
                evento="POST_COMMENT",
                destino_tipo="COMMUNITY_POST",
                destino_id=comment.post_id,
                metadata={
                    "actor_id": comment.user_id,
                    "actor_name": comment.user.username,
                },
            )
        return comment

    class Meta:
        model = Comentario
        fields = "__all__"
        read_only_fields = ["user"]


class ChatSerializer(serializers.ModelSerializer):
    def validate_usuarios(self, usuarios):
        request_user = self.context["request"].user
        if request_user not in usuarios:
            usuarios.append(request_user)
        return usuarios

    class Meta:
        model = Chat
        fields = "__all__"


class MensajeSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        message = super().create(validated_data)
        recipients = message.chat.usuarios.exclude(id=message.user_id)
        for recipient in recipients:
            notify(
                recipient,
                "mensaje",
                f"Recibiste un nuevo mensaje de {message.user.username}.",
                evento="CHAT_MESSAGE",
                destino_tipo="CHAT",
                destino_id=message.chat_id,
                metadata={
                    "actor_id": message.user_id,
                    "actor_name": message.user.username,
                },
            )
        return message

    def validate_chat(self, chat):
        if not chat.usuarios.filter(id=self.context["request"].user.id).exists():
            raise serializers.ValidationError("No perteneces a este chat.")
        return chat

    class Meta:
        model = Mensaje
        fields = "__all__"
        read_only_fields = ["user"]
