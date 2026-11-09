import graphene
from django.db import IntegrityError
from django.db.models import Q
from graphene_django import DjangoObjectType
from graphql import GraphQLError
from rest_framework.exceptions import NotFound
from .models import (
    ColeccionMaestra, 
    PiezaCatalogo, 
    ColeccionUsuario, 
    PiezaInventario, 
    PiezaFoto, 
    Favorito
)
from .serializers import (
    ColeccionMaestraSerializer,
    ColeccionUsuarioSerializer,
    PiezaCatalogoSerializer,
    PiezaInventarioSerializer,
    FavoritoSerializer,
)
from config.graphql_mutations import require_owner, serializer_save
from config.exceptions import get_request_id
from config.exceptions import Conflict
from config.media import resolve_media_url
from .favorites import favorite_is_available

class ColeccionMaestraType(DjangoObjectType):
    imagen = graphene.String()

    class Meta:
        model = ColeccionMaestra
        fields = "__all__"

    def resolve_imagen(self, info):
        return resolve_media_url(self.imagen, request=info.context)

class PiezaCatalogoType(DjangoObjectType):
    class Meta:
        model = PiezaCatalogo
        fields = "__all__"

class ColeccionUsuarioType(DjangoObjectType):
    class Meta:
        model = ColeccionUsuario
        fields = "__all__"

class PiezaInventarioType(DjangoObjectType):
    class Meta:
        model = PiezaInventario
        fields = "__all__"

class PiezaFotoType(DjangoObjectType):
    archivo = graphene.String()

    class Meta:
        model = PiezaFoto
        fields = "__all__"

    def resolve_archivo(self, info):
        return resolve_media_url(self.archivo, request=info.context)

class FavoriteTargetType(graphene.Enum):
    PIEZA = "PIEZA"
    COLECCION = "COLECCION"


def graphql_favorite_available(favorite, info):
    if not hasattr(favorite, "_favorite_graphql_available"):
        favorite._favorite_graphql_available = favorite_is_available(
            favorite, info.context.user
        )
    return favorite._favorite_graphql_available


class FavoritoType(graphene.ObjectType):
    id = graphene.ID(required=True)
    tipo = graphene.Field(FavoriteTargetType, required=True)
    objetivo_id = graphene.ID(required=True)
    pieza_inventario = graphene.Field(PiezaInventarioType)
    coleccion_maestra = graphene.Field(ColeccionMaestraType)
    disponible = graphene.Boolean(required=True)

    def resolve_tipo(self, info):
        return "PIEZA" if self.pieza_inventario_id else "COLECCION"

    def resolve_objetivo_id(self, info):
        return self.pieza_inventario_id or self.coleccion_maestra_id

    def resolve_pieza_inventario(self, info):
        return self.pieza_inventario if graphql_favorite_available(self, info) else None

    def resolve_coleccion_maestra(self, info):
        return self.coleccion_maestra if graphql_favorite_available(self, info) else None

    def resolve_disponible(self, info):
        return graphql_favorite_available(self, info)

class Query(graphene.ObjectType):
    colecciones_maestras = graphene.List(ColeccionMaestraType)
    piezas_catalogo = graphene.List(PiezaCatalogoType)
    colecciones_usuario = graphene.List(ColeccionUsuarioType)
    piezas_inventario = graphene.List(PiezaInventarioType)
    piezas_foto = graphene.List(PiezaFotoType)
    favoritos = graphene.List(FavoritoType, tipo=FavoriteTargetType())

    def resolve_colecciones_maestras(self, info):
        user = info.context.user
        return ColeccionMaestra.objects.filter(
            Q(tipo="global")
            | Q(propietario=user)
            | Q(coleccionusuario__user=user)
            | Q(coleccionusuario__publicacionmarket__isnull=False)
        ).distinct()

    def resolve_piezas_catalogo(self, info):
        user = info.context.user
        return PiezaCatalogo.objects.filter(
            Q(coleccion__tipo="global")
            | Q(coleccion__propietario=user)
            | Q(coleccion__coleccionusuario__user=user)
            | Q(piezainventario__publicacionmarket__isnull=False)
            | Q(coleccion__coleccionusuario__publicacionmarket__isnull=False)
        ).distinct()

    def resolve_colecciones_usuario(self, info):
        return ColeccionUsuario.objects.filter(
            Q(user=info.context.user) | Q(publicacionmarket__isnull=False)
        ).distinct()

    def resolve_piezas_inventario(self, info):
        return PiezaInventario.objects.filter(
            Q(user=info.context.user) | Q(publicacionmarket__isnull=False)
        ).distinct()

    def resolve_piezas_foto(self, info):
        return PiezaFoto.objects.filter(
            Q(pieza_inventario__user=info.context.user)
            | Q(pieza_inventario__publicacionmarket__isnull=False)
        ).distinct()

    def resolve_favoritos(self, info, tipo=None):
        queryset = Favorito.objects.filter(user=info.context.user).select_related(
            "pieza_inventario",
            "coleccion_maestra",
        )
        favorite_type = getattr(tipo, "value", tipo)
        if favorite_type == "PIEZA":
            queryset = queryset.filter(pieza_inventario__isnull=False)
        elif favorite_type == "COLECCION":
            queryset = queryset.filter(coleccion_maestra__isnull=False)
        return queryset


class FavoritoInput(graphene.InputObjectType):
    pieza_inventario_id = graphene.ID()
    coleccion_maestra_id = graphene.ID()


def save_favorite(info, data):
    try:
        return serializer_save(
            FavoritoSerializer,
            info,
            data,
            user=info.context.user,
        )
    except (Conflict, IntegrityError) as exc:
        raise GraphQLError(
            str(getattr(exc, "detail", "Este recurso ya está en tus favoritos.")),
            extensions={
                "code": "CONFLICT",
                "request_id": get_request_id(info.context),
            },
        ) from exc
    except NotFound as exc:
        raise GraphQLError(
            "El contenido solicitado ya no está disponible o no existe.",
            extensions={
                "code": "NOT_FOUND",
                "request_id": get_request_id(info.context),
            },
        ) from exc


class CreateFavorito(graphene.Mutation):
    class Arguments:
        input = FavoritoInput(required=True)

    favorito = graphene.Field(FavoritoType, required=True)

    @classmethod
    def mutate(cls, root, info, input):
        data = dict(input)
        if "pieza_inventario_id" in data:
            data["pieza_inventario"] = data.pop("pieza_inventario_id")
        if "coleccion_maestra_id" in data:
            data["coleccion_maestra"] = data.pop("coleccion_maestra_id")
        return cls(favorito=save_favorite(info, data))


class DeleteFavorito(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    ok = graphene.Boolean(required=True)

    @classmethod
    def mutate(cls, root, info, id):
        try:
            favorite = Favorito.objects.get(pk=id, user=info.context.user)
        except Favorito.DoesNotExist as exc:
            raise GraphQLError(
                "El contenido solicitado ya no está disponible o no existe.",
                extensions={
                    "code": "NOT_FOUND",
                    "request_id": get_request_id(info.context),
                },
            ) from exc
        favorite.delete()
        return cls(ok=True)


class ColeccionMaestraInput(graphene.InputObjectType):
    nombre = graphene.String(required=True)
    categoria = graphene.String(required=True)
    total_piezas = graphene.Int()
    tipo = graphene.String()


class CreateColeccionMaestra(graphene.Mutation):
    class Arguments:
        input = ColeccionMaestraInput(required=True)

    coleccion = graphene.Field(ColeccionMaestraType)

    @classmethod
    def mutate(cls, root, info, input):
        coleccion = serializer_save(
            ColeccionMaestraSerializer,
            info,
            input,
            propietario=info.context.user,
        )
        return cls(coleccion=coleccion)


class UpdateColeccionMaestra(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        input = ColeccionMaestraInput(required=True)

    coleccion = graphene.Field(ColeccionMaestraType)

    @classmethod
    def mutate(cls, root, info, id, input):
        coleccion = ColeccionMaestra.objects.get(pk=id)
        require_owner(coleccion.propietario_id == info.context.user.id)
        coleccion = serializer_save(
            ColeccionMaestraSerializer, info, input, instance=coleccion
        )
        return cls(coleccion=coleccion)


class DeleteColeccionMaestra(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    ok = graphene.Boolean(required=True)

    @classmethod
    def mutate(cls, root, info, id):
        coleccion = ColeccionMaestra.objects.get(pk=id)
        require_owner(coleccion.propietario_id == info.context.user.id)
        coleccion.delete()
        return cls(ok=True)


class JoinColeccion(graphene.Mutation):
    class Arguments:
        coleccion_id = graphene.ID(required=True)

    participacion = graphene.Field(ColeccionUsuarioType)

    @classmethod
    def mutate(cls, root, info, coleccion_id):
        participacion = serializer_save(
            ColeccionUsuarioSerializer,
            info,
            {"coleccion": coleccion_id},
            user=info.context.user,
        )
        return cls(participacion=participacion)


class LeaveColeccion(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    ok = graphene.Boolean(required=True)

    @classmethod
    def mutate(cls, root, info, id):
        participacion = ColeccionUsuario.objects.get(pk=id)
        require_owner(participacion.user_id == info.context.user.id)
        participacion.delete()
        return cls(ok=True)


class PiezaCatalogoInput(graphene.InputObjectType):
    coleccion_id = graphene.ID(required=True)
    numero_item = graphene.String(required=True)
    nombre = graphene.String(required=True)
    sku_base = graphene.String(required=True)


class CreatePiezaCatalogo(graphene.Mutation):
    class Arguments:
        input = PiezaCatalogoInput(required=True)

    pieza = graphene.Field(PiezaCatalogoType)

    @classmethod
    def mutate(cls, root, info, input):
        data = dict(input)
        data["coleccion"] = data.pop("coleccion_id")
        pieza = serializer_save(PiezaCatalogoSerializer, info, data)
        return cls(pieza=pieza)


class PiezaInventarioInput(graphene.InputObjectType):
    coleccion_usuario_id = graphene.ID(required=True)
    pieza_catalogo_id = graphene.ID(required=True)
    nombre_personalizado = graphene.String()
    sku = graphene.String(required=True)
    estado_adquisicion = graphene.String(required=True)
    visibilidad = graphene.String(required=True)
    condicion = graphene.String(required=True)
    talla = graphene.String()


class CreatePiezaInventario(graphene.Mutation):
    class Arguments:
        input = PiezaInventarioInput(required=True)

    pieza = graphene.Field(PiezaInventarioType)

    @classmethod
    def mutate(cls, root, info, input):
        data = dict(input)
        data["coleccion_usuario"] = data.pop("coleccion_usuario_id")
        data["pieza_catalogo"] = data.pop("pieza_catalogo_id")
        pieza = serializer_save(
            PiezaInventarioSerializer, info, data, user=info.context.user
        )
        return cls(pieza=pieza)


class UpdatePiezaInventario(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        nombre_personalizado = graphene.String()
        condicion = graphene.String()
        visibilidad = graphene.String()

    pieza = graphene.Field(PiezaInventarioType)

    @classmethod
    def mutate(cls, root, info, id, **changes):
        pieza = PiezaInventario.objects.get(pk=id)
        require_owner(pieza.user_id == info.context.user.id)
        pieza = serializer_save(
            PiezaInventarioSerializer, info, changes, instance=pieza
        )
        return cls(pieza=pieza)


class DeletePiezaInventario(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    ok = graphene.Boolean(required=True)

    @classmethod
    def mutate(cls, root, info, id):
        pieza = PiezaInventario.objects.get(pk=id)
        require_owner(pieza.user_id == info.context.user.id)
        pieza.delete()
        return cls(ok=True)


class Mutation(graphene.ObjectType):
    create_coleccion_maestra = CreateColeccionMaestra.Field()
    update_coleccion_maestra = UpdateColeccionMaestra.Field()
    delete_coleccion_maestra = DeleteColeccionMaestra.Field()
    join_coleccion = JoinColeccion.Field()
    leave_coleccion = LeaveColeccion.Field()
    create_pieza_catalogo = CreatePiezaCatalogo.Field()
    create_pieza_inventario = CreatePiezaInventario.Field()
    update_pieza_inventario = UpdatePiezaInventario.Field()
    delete_pieza_inventario = DeletePiezaInventario.Field()
    crear_favorito = CreateFavorito.Field()
    eliminar_favorito = DeleteFavorito.Field()
