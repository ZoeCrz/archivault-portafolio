import graphene
from django.db.models import Q
from django.core.paginator import EmptyPage, Paginator
from graphene_django import DjangoObjectType
from graphql import GraphQLError
from rest_framework.exceptions import ValidationError
from .models import PublicacionMarket, Oferta
from .serializers import PublicacionMarketSerializer, OfertaSerializer
from config.graphql_mutations import require_owner, serializer_save
from config.exceptions import get_request_id, normalize_error_fields
from .services import (
    accept_offer,
    complete_offer,
    filter_marketplace_publications,
    marketplace_publications_for,
    reject_offer,
    visible_publications_for,
)

class PublicacionMarketType(DjangoObjectType):
    class Meta:
        model = PublicacionMarket
        fields = "__all__"

class OfertaType(DjangoObjectType):
    class Meta:
        model = Oferta
        fields = "__all__"


class MarketplaceCollectionType(graphene.ObjectType):
    id = graphene.ID(required=True)
    coleccion_usuario_id = graphene.ID()
    nombre = graphene.String(required=True)


class MarketplaceSellerType(graphene.ObjectType):
    id = graphene.ID(required=True)
    nombre = graphene.String(required=True)


class MarketplacePublicationType(graphene.ObjectType):
    id = graphene.ID(required=True)
    tipo = graphene.String(required=True)
    objetivo_id = graphene.ID(required=True)
    nombre = graphene.String(required=True)
    sku = graphene.String()
    coleccion = graphene.Field(MarketplaceCollectionType, required=True)
    descripcion = graphene.String(required=True)
    condicion = graphene.String(required=True)
    imagen = graphene.List(graphene.NonNull(graphene.String), required=True)
    vendedor = graphene.Field(MarketplaceSellerType, required=True)
    precio = graphene.Decimal(required=True)
    categoria = graphene.String(required=True)
    estado = graphene.String(required=True)
    estado_objetivo = graphene.String()
    es_favorito = graphene.Boolean(required=True)
    fecha_publicacion = graphene.DateTime(required=True)

    @staticmethod
    def _data(root, info):
        cache_name = "_marketplace_graphql_data"
        if not hasattr(root, cache_name):
            setattr(
                root,
                cache_name,
                PublicacionMarketSerializer(root, context={"request": info.context}).data,
            )
        return getattr(root, cache_name)

    def resolve_tipo(root, info):
        return MarketplacePublicationType._data(root, info)["tipo"]

    def resolve_objetivo_id(root, info):
        return MarketplacePublicationType._data(root, info)["objetivo_id"]

    def resolve_nombre(root, info):
        return MarketplacePublicationType._data(root, info)["nombre"]

    def resolve_sku(root, info):
        return MarketplacePublicationType._data(root, info)["sku"]

    def resolve_coleccion(root, info):
        return MarketplacePublicationType._data(root, info)["coleccion"]

    def resolve_imagen(root, info):
        return MarketplacePublicationType._data(root, info)["imagen"]

    def resolve_vendedor(root, info):
        return MarketplacePublicationType._data(root, info)["vendedor"]

    def resolve_categoria(root, info):
        return MarketplacePublicationType._data(root, info)["categoria"]

    def resolve_estado_objetivo(root, info):
        return MarketplacePublicationType._data(root, info)["estado_objetivo"]

    def resolve_es_favorito(root, info):
        return MarketplacePublicationType._data(root, info)["es_favorito"]


class MarketplacePublicationFilters(graphene.InputObjectType):
    q = graphene.String()
    tipo = graphene.String()
    estado = graphene.String()
    condicion = graphene.String()
    categoria = graphene.String()
    coleccion_id = graphene.ID()
    precio_min = graphene.Decimal()
    precio_max = graphene.Decimal()
    favoritos = graphene.Boolean()
    orden = graphene.String()


class MarketplacePublicationPage(graphene.ObjectType):
    total = graphene.Int(required=True)
    page = graphene.Int(required=True)
    page_size = graphene.Int(required=True)
    results = graphene.List(MarketplacePublicationType, required=True)

class Query(graphene.ObjectType):
    # Consulta legada conservada temporalmente para clientes existentes.
    publicaciones_market = graphene.List(PublicacionMarketType)
    publicaciones_marketplace = graphene.Field(
        MarketplacePublicationPage,
        filtros=MarketplacePublicationFilters(),
        page=graphene.Int(default_value=1),
        page_size=graphene.Int(default_value=24),
    )
    ofertas = graphene.List(OfertaType)

    def resolve_publicaciones_market(self, info):
        return visible_publications_for(info.context.user)

    def resolve_publicaciones_marketplace(
        self, info, filtros=None, page=1, page_size=24
    ):
        errors = {}
        if page < 1:
            errors["page"] = ["La página debe ser igual o mayor que uno."]
        if page_size < 1 or page_size > 100:
            errors["page_size"] = ["El tamaño de página debe estar entre 1 y 100."]
        if errors:
            raise GraphQLError(
                "Revisa los datos indicados.",
                extensions={
                    "code": "VALIDATION_ERROR",
                    "fields": errors,
                    "request_id": get_request_id(info.context),
                },
            )

        params = dict(filtros or {})
        if "coleccion_id" in params:
            params["coleccion"] = params.pop("coleccion_id")
        try:
            queryset = filter_marketplace_publications(
                marketplace_publications_for(info.context.user), params
            )
        except ValidationError as exc:
            raise GraphQLError(
                "Revisa los datos indicados.",
                extensions={
                    "code": "VALIDATION_ERROR",
                    "fields": normalize_error_fields(exc.detail),
                    "request_id": get_request_id(info.context),
                },
            ) from exc

        paginator = Paginator(queryset, page_size)
        try:
            current_page = paginator.page(page)
        except EmptyPage as exc:
            raise GraphQLError(
                "La página solicitada no está disponible.",
                extensions={
                    "code": "VALIDATION_ERROR",
                    "fields": {"page": ["La página solicitada no está disponible."]},
                    "request_id": get_request_id(info.context),
                },
            ) from exc
        return MarketplacePublicationPage(
            total=paginator.count,
            page=current_page.number,
            page_size=page_size,
            results=list(current_page.object_list),
        )

    def resolve_ofertas(self, info):
        user = info.context.user
        return Oferta.objects.filter(
            Q(comprador=user)
            | Q(publicacion__vendedor=user)
        ).distinct()


def publication_belongs_to(publication, user):
    return publication.vendedor_id == user.id


class PublicacionInput(graphene.InputObjectType):
    pieza_inventario_id = graphene.ID()
    coleccion_usuario_id = graphene.ID()
    precio = graphene.Decimal(required=True)
    estado = graphene.String(required=True)
    descripcion = graphene.String()
    condicion = graphene.String()


class CreatePublicacion(graphene.Mutation):
    class Arguments:
        input = PublicacionInput(required=True)

    publicacion = graphene.Field(PublicacionMarketType)

    @classmethod
    def mutate(cls, root, info, input):
        data = dict(input)
        if "pieza_inventario_id" in data:
            data["pieza_inventario"] = data.pop("pieza_inventario_id")
        if "coleccion_usuario_id" in data:
            data["coleccion_usuario"] = data.pop("coleccion_usuario_id")
        publicacion = serializer_save(
            PublicacionMarketSerializer,
            info,
            data,
            vendedor=info.context.user,
            estado="ACTIVA",
        )
        return cls(publicacion=publicacion)


class UpdatePublicacion(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        precio = graphene.Decimal()
        estado = graphene.String()
        descripcion = graphene.String()
        condicion = graphene.String()

    publicacion = graphene.Field(PublicacionMarketType)

    @classmethod
    def mutate(cls, root, info, id, **changes):
        publicacion = PublicacionMarket.objects.get(pk=id)
        require_owner(publication_belongs_to(publicacion, info.context.user))
        publicacion = serializer_save(
            PublicacionMarketSerializer, info, changes, instance=publicacion
        )
        return cls(publicacion=publicacion)


class DeletePublicacion(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    ok = graphene.Boolean(required=True)

    @classmethod
    def mutate(cls, root, info, id):
        publicacion = PublicacionMarket.objects.get(pk=id)
        require_owner(publication_belongs_to(publicacion, info.context.user))
        publicacion.delete()
        return cls(ok=True)


class OfertaInput(graphene.InputObjectType):
    publicacion_id = graphene.ID(required=True)
    monto = graphene.Decimal(required=True)
    estado = graphene.String(required=True)


class CreateOferta(graphene.Mutation):
    class Arguments:
        input = OfertaInput(required=True)

    oferta = graphene.Field(OfertaType)

    @classmethod
    def mutate(cls, root, info, input):
        data = dict(input)
        data["publicacion"] = data.pop("publicacion_id")
        oferta = serializer_save(
            OfertaSerializer,
            info,
            data,
            comprador=info.context.user,
            estado="PENDIENTE",
        )
        return cls(oferta=oferta)


class UpdateOfertaEstado(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        estado = graphene.String(required=True)

    oferta = graphene.Field(OfertaType)

    @classmethod
    def mutate(cls, root, info, id, estado):
        transitions = {
            "ACEPTADA": accept_offer,
            "RECHAZADA": reject_offer,
            "COMPLETADA": complete_offer,
        }
        if estado not in transitions:
            require_owner(False, "Transición de oferta no permitida.")
        oferta = transitions[estado](id, info.context.user)
        return cls(oferta=oferta)


class Mutation(graphene.ObjectType):
    create_publicacion = CreatePublicacion.Field()
    update_publicacion = UpdatePublicacion.Field()
    delete_publicacion = DeletePublicacion.Field()
    create_oferta = CreateOferta.Field()
    update_oferta_estado = UpdateOfertaEstado.Field()
