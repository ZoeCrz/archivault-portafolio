from rest_framework import serializers, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from config.permissions import IsResourceOwnerOrReadOnly
from .models import Post, PostMedia, PostLike, Comentario, Chat, Mensaje
from .serializers import (
    PostSerializer,
    PostMediaSerializer,
    PostLikeSerializer,
    ComentarioSerializer,
    ChatSerializer,
    MensajeSerializer,
    MarketplaceNewsSerializer,
    TopCollectorSerializer,
)
from .insights import latest_marketplace_publications, top_collectors


class CommunitySummaryView(APIView):
    def get(self, request):
        news = MarketplaceNewsSerializer(
            latest_marketplace_publications(request.user), many=True
        ).data
        collectors = TopCollectorSerializer(top_collectors(), many=True).data
        return Response(
            {
                "novedades_marketplace": news,
                "coleccionistas_top": collectors,
            }
        )


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsResourceOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def is_owner(self, obj, user):
        return obj.user_id == user.id


class PostMediaViewSet(viewsets.ModelViewSet):
    queryset = PostMedia.objects.all()
    serializer_class = PostMediaSerializer
    permission_classes = [IsResourceOwnerOrReadOnly]

    def is_owner(self, obj, user):
        return obj.post.user_id == user.id


class PostLikeViewSet(viewsets.ModelViewSet):
    queryset = PostLike.objects.all()
    serializer_class = PostLikeSerializer
    permission_classes = [IsResourceOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def is_owner(self, obj, user):
        return obj.user_id == user.id


class ComentarioViewSet(viewsets.ModelViewSet):
    queryset = Comentario.objects.all()
    serializer_class = ComentarioSerializer
    permission_classes = [IsResourceOwnerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def is_owner(self, obj, user):
        return obj.user_id == user.id


class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer

    def get_queryset(self):
        return Chat.objects.filter(usuarios=self.request.user)


class MensajeViewSet(viewsets.ModelViewSet):
    queryset = Mensaje.objects.all()
    serializer_class = MensajeSerializer
    permission_classes = [IsResourceOwnerOrReadOnly]

    def get_queryset(self):
        queryset = Mensaje.objects.filter(chat__usuarios=self.request.user).order_by("id")
        chat_id = self.request.query_params.get("chat")
        if chat_id:
            queryset = queryset.filter(chat_id=chat_id)
        after = self.request.query_params.get("after")
        if after:
            try:
                queryset = queryset.filter(id__gt=int(after))
            except ValueError as exc:
                raise serializers.ValidationError(
                    {"after": "Debe ser un identificador numérico."}
                ) from exc
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def is_owner(self, obj, user):
        return obj.user_id == user.id
