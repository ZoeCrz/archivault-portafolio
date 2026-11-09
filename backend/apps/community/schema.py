import graphene
from graphene_django import DjangoObjectType
from .models import Post, PostMedia, PostLike, Comentario, Chat, Mensaje
from .serializers import (
    PostSerializer,
    PostLikeSerializer,
    ComentarioSerializer,
    ChatSerializer,
    MensajeSerializer,
)
from config.graphql_mutations import require_owner, serializer_save
from config.media import resolve_media_url
from .insights import latest_marketplace_publications, top_collectors

class PostType(DjangoObjectType):
    class Meta:
        model = Post
        fields = "__all__"

class PostMediaType(DjangoObjectType):
    archivo = graphene.String()

    class Meta:
        model = PostMedia
        fields = "__all__"

    def resolve_archivo(self, info):
        return resolve_media_url(self.archivo, request=info.context)

class PostLikeType(DjangoObjectType):
    class Meta:
        model = PostLike
        fields = "__all__"

class ComentarioType(DjangoObjectType):
    imagen = graphene.String()

    class Meta:
        model = Comentario
        fields = "__all__"

    def resolve_imagen(self, info):
        return resolve_media_url(self.imagen, request=info.context)

class ChatType(DjangoObjectType):
    class Meta:
        model = Chat
        fields = "__all__"

class MensajeType(DjangoObjectType):
    class Meta:
        model = Mensaje
        fields = "__all__"


class MarketplaceNewsType(graphene.ObjectType):
    id = graphene.ID(required=True)
    tipo = graphene.String(required=True)
    nombre = graphene.String(required=True)
    precio = graphene.Decimal(required=True)
    fecha_publicacion = graphene.DateTime(required=True)

    def resolve_tipo(self, info):
        return self.insight_tipo

    def resolve_nombre(self, info):
        return self.insight_nombre


class TopCollectorType(graphene.ObjectType):
    id = graphene.ID(required=True)
    nombre = graphene.String(required=True)
    likes_recibidos = graphene.Int(required=True)
    comentarios_recibidos = graphene.Int(required=True)
    score = graphene.Int(required=True)

    def resolve_nombre(self, info):
        return self.username

class Query(graphene.ObjectType):
    posts = graphene.List(PostType)
    post_media = graphene.List(PostMediaType)
    post_likes = graphene.List(PostLikeType)
    comentarios = graphene.List(ComentarioType)
    chats = graphene.List(ChatType)
    mensajes = graphene.List(MensajeType)
    novedades_marketplace = graphene.List(MarketplaceNewsType, required=True)
    coleccionistas_top = graphene.List(TopCollectorType, required=True)

    def resolve_posts(self, info):
        return Post.objects.all()

    def resolve_post_media(self, info):
        return PostMedia.objects.all()

    def resolve_post_likes(self, info):
        return PostLike.objects.all()

    def resolve_comentarios(self, info):
        return Comentario.objects.all()

    def resolve_chats(self, info):
        return Chat.objects.filter(usuarios=info.context.user)

    def resolve_mensajes(self, info):
        return Mensaje.objects.filter(chat__usuarios=info.context.user)

    def resolve_novedades_marketplace(self, info):
        return latest_marketplace_publications(info.context.user)

    def resolve_coleccionistas_top(self, info):
        return top_collectors()


class CreatePost(graphene.Mutation):
    class Arguments:
        contenido = graphene.String(required=True)

    post = graphene.Field(PostType)

    @classmethod
    def mutate(cls, root, info, contenido):
        post = serializer_save(
            PostSerializer,
            info,
            {"contenido": contenido},
            user=info.context.user,
        )
        return cls(post=post)


class UpdatePost(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        contenido = graphene.String(required=True)

    post = graphene.Field(PostType)

    @classmethod
    def mutate(cls, root, info, id, contenido):
        post = Post.objects.get(pk=id)
        require_owner(post.user_id == info.context.user.id)
        post = serializer_save(
            PostSerializer, info, {"contenido": contenido}, instance=post
        )
        return cls(post=post)


class DeletePost(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    ok = graphene.Boolean(required=True)

    @classmethod
    def mutate(cls, root, info, id):
        post = Post.objects.get(pk=id)
        require_owner(post.user_id == info.context.user.id)
        post.delete()
        return cls(ok=True)


class CreateComentario(graphene.Mutation):
    class Arguments:
        post_id = graphene.ID(required=True)
        contenido = graphene.String(required=True)

    comentario = graphene.Field(ComentarioType)

    @classmethod
    def mutate(cls, root, info, post_id, contenido):
        comentario = serializer_save(
            ComentarioSerializer,
            info,
            {"post": post_id, "contenido": contenido},
            user=info.context.user,
        )
        return cls(comentario=comentario)


class DeleteComentario(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    ok = graphene.Boolean(required=True)

    @classmethod
    def mutate(cls, root, info, id):
        comentario = Comentario.objects.get(pk=id)
        require_owner(comentario.user_id == info.context.user.id)
        comentario.delete()
        return cls(ok=True)


class TogglePostLike(graphene.Mutation):
    class Arguments:
        post_id = graphene.ID(required=True)

    active = graphene.Boolean(required=True)

    @classmethod
    def mutate(cls, root, info, post_id):
        existing = PostLike.objects.filter(
            post_id=post_id, user=info.context.user
        ).first()
        if existing:
            existing.delete()
            return cls(active=False)
        serializer_save(
            PostLikeSerializer,
            info,
            {"post": post_id},
            user=info.context.user,
        )
        return cls(active=True)


class CreateChat(graphene.Mutation):
    class Arguments:
        user_ids = graphene.List(graphene.NonNull(graphene.ID), required=True)

    chat = graphene.Field(ChatType)

    @classmethod
    def mutate(cls, root, info, user_ids):
        chat = serializer_save(ChatSerializer, info, {"usuarios": user_ids})
        return cls(chat=chat)


class CreateMensaje(graphene.Mutation):
    class Arguments:
        chat_id = graphene.ID(required=True)
        contenido = graphene.String(required=True)

    mensaje = graphene.Field(MensajeType)

    @classmethod
    def mutate(cls, root, info, chat_id, contenido):
        mensaje = serializer_save(
            MensajeSerializer,
            info,
            {"chat": chat_id, "contenido": contenido},
            user=info.context.user,
        )
        return cls(mensaje=mensaje)


class Mutation(graphene.ObjectType):
    create_post = CreatePost.Field()
    update_post = UpdatePost.Field()
    delete_post = DeletePost.Field()
    create_comentario = CreateComentario.Field()
    delete_comentario = DeleteComentario.Field()
    toggle_post_like = TogglePostLike.Field()
    create_chat = CreateChat.Field()
    create_mensaje = CreateMensaje.Field()
