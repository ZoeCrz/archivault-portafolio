import graphene
from graphene.types.generic import GenericScalar
from graphene_django import DjangoObjectType
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Profile, MetodoPago, Resena
from .serializers import ProfileSerializer, MetodoPagoSerializer, ResenaSerializer
from config.graphql_mutations import require_owner, serializer_save
from config.media import resolve_media_url

class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ("id", "username")

class ProfileType(DjangoObjectType):
    avatar = graphene.String()

    class Meta:
        model = Profile
        fields = "__all__"

    def resolve_avatar(self, info):
        return resolve_media_url(self.avatar, request=info.context)

class MetodoPagoType(DjangoObjectType):
    class Meta:
        model = MetodoPago
        fields = "__all__"

class ResenaType(DjangoObjectType):
    class Meta:
        model = Resena
        fields = "__all__"

class Query(graphene.ObjectType):
    usuarios = graphene.List(UserType)
    perfiles = graphene.List(ProfileType)
    metodos_pago = graphene.List(MetodoPagoType)
    resenas = graphene.List(ResenaType)
    perfil_resumen = GenericScalar(profile_id=graphene.ID(required=True))
    perfil_actividad = GenericScalar(
        profile_id=graphene.ID(required=True),
        tipo=graphene.String(required=True),
        page=graphene.Int(default_value=1),
        page_size=graphene.Int(default_value=10),
    )

    def resolve_usuarios(self, info):
        return User.objects.all()

    def resolve_perfiles(self, info):
        return Profile.objects.filter(Q(perfil_publico=True) | Q(user=info.context.user))

    def resolve_metodos_pago(self, info):
        return MetodoPago.objects.filter(user=info.context.user)

    def resolve_resenas(self, info):
        user = info.context.user
        return Resena.objects.filter(
            Q(emisor=user) | Q(receptor=user) | Q(receptor__profile__perfil_publico=True)
        ).distinct()

    def resolve_perfil_resumen(self, info, profile_id):
        from .profile_insights import build_profile_summary, get_accessible_profile
        profile = get_accessible_profile(info.context.user, profile_id)
        return build_profile_summary(profile, info.context)

    def resolve_perfil_actividad(self, info, profile_id, tipo, page=1, page_size=10):
        from django.core.paginator import Paginator
        from rest_framework.exceptions import ValidationError
        from .profile_insights import get_accessible_profile, profile_activity_queryset, serialize_profile_activity
        if page < 1 or page_size < 1 or page_size > 50:
            raise ValidationError({"page": ["Selecciona una página y tamaño válidos."]})
        profile = get_accessible_profile(info.context.user, profile_id)
        paginator = Paginator(profile_activity_queryset(profile, info.context.user, tipo), page_size)
        selected = paginator.get_page(page)
        return {"count": paginator.count, "page": selected.number, "num_pages": paginator.num_pages, "results": serialize_profile_activity(selected.object_list, tipo)}


class ProfileInput(graphene.InputObjectType):
    biografia = graphene.String()
    ubicacion = graphene.String()
    perfil_publico = graphene.Boolean()


class SaveProfile(graphene.Mutation):
    class Arguments:
        input = ProfileInput(required=True)

    profile = graphene.Field(ProfileType)

    @classmethod
    def mutate(cls, root, info, input):
        profile = Profile.objects.filter(user=info.context.user).first()
        profile = serializer_save(
            ProfileSerializer,
            info,
            input,
            instance=profile,
            user=info.context.user,
        )
        return cls(profile=profile)


class MetodoPagoInput(graphene.InputObjectType):
    plataforma = graphene.String(required=True)
    alias_pago = graphene.String()
    correo_pago = graphene.String()
    activo = graphene.Boolean()


class CreateMetodoPago(graphene.Mutation):
    class Arguments:
        input = MetodoPagoInput(required=True)

    metodo_pago = graphene.Field(MetodoPagoType)

    @classmethod
    def mutate(cls, root, info, input):
        metodo = serializer_save(
            MetodoPagoSerializer, info, input, user=info.context.user
        )
        return cls(metodo_pago=metodo)


class ResenaInput(graphene.InputObjectType):
    receptor_id = graphene.ID(required=True)
    puntuacion = graphene.Int(required=True)
    comentario = graphene.String()


class CreateResena(graphene.Mutation):
    class Arguments:
        input = ResenaInput(required=True)

    resena = graphene.Field(ResenaType)

    @classmethod
    def mutate(cls, root, info, input):
        data = dict(input)
        data["receptor"] = data.pop("receptor_id")
        resena = serializer_save(
            ResenaSerializer, info, data, emisor=info.context.user
        )
        return cls(resena=resena)


class DeleteResena(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    ok = graphene.Boolean(required=True)

    @classmethod
    def mutate(cls, root, info, id):
        resena = Resena.objects.get(pk=id)
        require_owner(resena.emisor_id == info.context.user.id)
        resena.delete()
        return cls(ok=True)


class Mutation(graphene.ObjectType):
    save_profile = SaveProfile.Field()
    create_metodo_pago = CreateMetodoPago.Field()
    create_resena = CreateResena.Field()
    delete_resena = DeleteResena.Field()
