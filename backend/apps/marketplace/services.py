from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Case, CharField, Exists, OuterRef, Prefetch, Q, Value, When
from django.db.models.functions import Coalesce, Lower, NullIf, Trim
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.serializers import ValidationError

from apps.catalog.models import ColeccionUsuario, Favorito, PiezaFoto, PiezaInventario
from apps.catalog.progress import recalculate_progress
from apps.webhooks.notifications import notify
from config.exceptions import Conflict
from .models import Oferta, PublicacionMarket


def visible_publications_for(user):
    return PublicacionMarket.objects.filter(
        Q(estado__in=["ACTIVA", "RESERVADA"])
        | Q(vendedor=user)
        | Q(oferta__comprador=user)
    ).distinct()


PUBLICATION_ORDERING = {
    "recientes": ("-fecha_publicacion", "-id"),
    "antiguos": ("fecha_publicacion", "id"),
    "precio_asc": ("precio", "id"),
    "precio_desc": ("-precio", "-id"),
    "nombre_asc": ("_market_name", "id"),
}


def marketplace_name_expression():
    """Shared database expression for the public name of a listing target."""
    return Case(
        When(
            pieza_inventario__isnull=False,
            then=Coalesce(
                NullIf(Trim("pieza_inventario__nombre_personalizado"), Value("")),
                NullIf(Trim("pieza_inventario__pieza_catalogo__nombre"), Value("")),
                Value("Pieza sin nombre"),
            ),
        ),
        default=Coalesce(
            NullIf(Trim("coleccion_usuario__coleccion__nombre"), Value("")),
            Value("Colección sin nombre"),
        ),
        output_field=CharField(),
    )


def marketplace_resource_name(publication):
    """Resolve the same public target name for an already loaded publication."""
    if publication.pieza_inventario_id:
        piece = publication.pieza_inventario
        return (
            (piece.nombre_personalizado or "").strip()
            or (piece.pieza_catalogo.nombre or "").strip()
            or "Pieza sin nombre"
        )
    return (
        (publication.coleccion_usuario.coleccion.nombre or "").strip()
        or "Colección sin nombre"
    )


def marketplace_publications_for(user):
    """Return visible publications with every relation needed by read contracts."""
    photos = PiezaFoto.objects.only(
        "id", "pieza_inventario_id", "archivo", "url"
    ).order_by("id")
    favorite = Favorito.objects.filter(user=user).filter(
        Q(pieza_inventario_id=OuterRef("pieza_inventario_id"))
        | Q(
            coleccion_maestra_id=OuterRef(
                "coleccion_usuario__coleccion_id"
            )
        )
    )
    return (
        visible_publications_for(user)
        .select_related(
            "vendedor",
            "pieza_inventario__pieza_catalogo__coleccion",
            "pieza_inventario__coleccion_usuario__coleccion",
            "coleccion_usuario__coleccion",
        )
        .prefetch_related(
            Prefetch(
                "pieza_inventario__piezafoto_set",
                queryset=photos,
                to_attr="marketplace_photos",
            )
        )
        .annotate(
            es_favorito=Exists(favorite),
            _market_name=Lower(marketplace_name_expression())
        )
    )


def _single_value(params, name):
    value = params.get(name)
    return value.strip() if isinstance(value, str) else value


def _decimal_filter(params, name, errors):
    value = _single_value(params, name)
    if value in (None, ""):
        return None
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        errors[name] = ["Introduce un precio válido."]
        return None
    if not parsed.is_finite() or parsed < 0:
        errors[name] = ["El precio debe ser igual o mayor que cero."]
        return None
    return parsed


def filter_marketplace_publications(queryset, params):
    """Apply the shared REST/GraphQL marketplace filter contract."""
    errors = {}
    publication_type = _single_value(params, "tipo")
    state = _single_value(params, "estado")
    condition = _single_value(params, "condicion")
    collection = _single_value(params, "coleccion")
    ordering = _single_value(params, "orden") or "recientes"
    favorites = _single_value(params, "favoritos")

    if publication_type and publication_type not in {"PIEZA", "COLECCION"}:
        errors["tipo"] = ["Selecciona un tipo de publicación válido."]
    if state and state not in dict(PublicacionMarket.ESTADOS):
        errors["estado"] = ["Selecciona un estado de publicación válido."]
    if condition and condition not in dict(PublicacionMarket.CONDICIONES):
        errors["condicion"] = ["Selecciona una condición válida."]
    if ordering not in PUBLICATION_ORDERING:
        errors["orden"] = ["Selecciona un orden válido."]
    if collection not in (None, ""):
        try:
            collection = int(collection)
            if collection <= 0:
                raise ValueError
        except (TypeError, ValueError):
            errors["coleccion"] = ["Selecciona una colección válida."]
    favorite_value = None
    if favorites not in (None, ""):
        if favorites in (True, "true", "True", "1", 1):
            favorite_value = True
        elif favorites in (False, "false", "False", "0", 0):
            favorite_value = False
        else:
            errors["favoritos"] = ["Introduce un valor válido para favoritos."]

    minimum = _decimal_filter(params, "precio_min", errors)
    maximum = _decimal_filter(params, "precio_max", errors)
    if minimum is not None and maximum is not None and minimum > maximum:
        errors["precio_min"] = [
            "El precio mínimo no puede ser mayor que el precio máximo."
        ]
    if errors:
        raise ValidationError(errors)

    query = _single_value(params, "q")
    if query:
        queryset = queryset.filter(
            Q(pieza_inventario__nombre_personalizado__icontains=query)
            | Q(pieza_inventario__pieza_catalogo__nombre__icontains=query)
            | Q(pieza_inventario__sku__icontains=query)
            | Q(pieza_inventario__pieza_catalogo__coleccion__nombre__icontains=query)
            | Q(pieza_inventario__pieza_catalogo__coleccion__categoria__icontains=query)
            | Q(coleccion_usuario__coleccion__nombre__icontains=query)
            | Q(coleccion_usuario__coleccion__categoria__icontains=query)
            | Q(descripcion__icontains=query)
        )
    if publication_type == "PIEZA":
        queryset = queryset.filter(pieza_inventario__isnull=False)
    elif publication_type == "COLECCION":
        queryset = queryset.filter(coleccion_usuario__isnull=False)
    if state:
        queryset = queryset.filter(estado=state)
    if condition:
        queryset = queryset.filter(condicion=condition)
    category = _single_value(params, "categoria")
    if category:
        queryset = queryset.filter(
            Q(pieza_inventario__pieza_catalogo__coleccion__categoria__iexact=category)
            | Q(coleccion_usuario__coleccion__categoria__iexact=category)
        )
    if collection:
        queryset = queryset.filter(
            Q(pieza_inventario__pieza_catalogo__coleccion_id=collection)
            | Q(coleccion_usuario__coleccion_id=collection)
        )
    if minimum is not None:
        queryset = queryset.filter(precio__gte=minimum)
    if maximum is not None:
        queryset = queryset.filter(precio__lte=maximum)
    if favorite_value is not None:
        queryset = queryset.filter(es_favorito=favorite_value)
    return queryset.order_by(*PUBLICATION_ORDERING[ordering])


def _lock_offer(offer_id):
    try:
        return Oferta.objects.select_for_update().select_related(
            "comprador",
            "publicacion__vendedor",
            "publicacion__pieza_inventario__pieza_catalogo__coleccion",
            "publicacion__coleccion_usuario__coleccion",
        ).get(pk=offer_id)
    except Oferta.DoesNotExist as exc:
        raise NotFound() from exc


def _require_seller(offer, user):
    if offer.publicacion.vendedor_id != user.id:
        raise PermissionDenied("Sólo el vendedor puede realizar esta acción.")


def _offer_notification_metadata(offer, resource_name):
    return {
        "resource_type": "PIEZA" if offer.publicacion.pieza_inventario_id else "COLECCION",
        "resource_name": resource_name,
        "offer_id": offer.id,
        "amount": str(offer.monto),
    }


@transaction.atomic
def accept_offer(offer_id, user):
    offer = _lock_offer(offer_id)
    _require_seller(offer, user)
    if offer.estado != "PENDIENTE" or offer.publicacion.estado != "ACTIVA":
        raise Conflict("La oferta ya no puede aceptarse porque su estado cambió.")

    offer.estado = "ACEPTADA"
    offer.save(update_fields=["estado"])
    rejected_offers = list(Oferta.objects.filter(
        publicacion=offer.publicacion,
        estado="PENDIENTE",
    ).exclude(pk=offer.pk).select_related("comprador"))
    Oferta.objects.filter(pk__in=[item.pk for item in rejected_offers]).update(
        estado="RECHAZADA"
    )
    offer.publicacion.estado = "RESERVADA"
    offer.publicacion.save(update_fields=["estado"])
    resource_name = marketplace_resource_name(offer.publicacion)
    notify(
        offer.comprador,
        "oferta",
        f"Tu oferta por {resource_name} fue aceptada.",
        evento="OFFER_ACCEPTED",
        destino_tipo="MARKETPLACE_PUBLICATION",
        destino_id=offer.publicacion_id,
        metadata=_offer_notification_metadata(offer, resource_name),
    )
    for rejected in rejected_offers:
        rejected_name = marketplace_resource_name(rejected.publicacion)
        notify(
            rejected.comprador,
            "oferta",
            f"Tu oferta por {rejected_name} fue rechazada porque se aceptó otra propuesta.",
            evento="OFFER_REJECTED",
            destino_tipo="MARKETPLACE_PUBLICATION",
            destino_id=rejected.publicacion_id,
            metadata=_offer_notification_metadata(rejected, rejected_name),
        )
    return offer


@transaction.atomic
def reject_offer(offer_id, user):
    offer = _lock_offer(offer_id)
    _require_seller(offer, user)
    if offer.estado != "PENDIENTE":
        raise Conflict("La oferta ya no puede rechazarse porque su estado cambió.")
    offer.estado = "RECHAZADA"
    offer.save(update_fields=["estado"])
    resource_name = marketplace_resource_name(offer.publicacion)
    notify(
        offer.comprador,
        "oferta",
        f"Tu oferta por {resource_name} fue rechazada.",
        evento="OFFER_REJECTED",
        destino_tipo="MARKETPLACE_PUBLICATION",
        destino_id=offer.publicacion_id,
        metadata=_offer_notification_metadata(offer, resource_name),
    )
    return offer


def _transfer_piece(publication, buyer):
    piece = PiezaInventario.objects.select_for_update().get(
        pk=publication.pieza_inventario_id
    )
    participation, _ = ColeccionUsuario.objects.get_or_create(
        user=buyer,
        coleccion=piece.pieza_catalogo.coleccion,
    )
    piece.user = buyer
    piece.coleccion_usuario = participation
    piece.visibilidad = "PRIVADA"
    piece.save(update_fields=["user", "coleccion_usuario", "visibilidad"])


def _transfer_collection(publication, buyer):
    sold = ColeccionUsuario.objects.select_for_update().select_related("coleccion").get(
        pk=publication.coleccion_usuario_id
    )
    existing = ColeccionUsuario.objects.filter(
        user=buyer,
        coleccion=sold.coleccion,
    ).first()

    if existing:
        PiezaInventario.objects.filter(coleccion_usuario=sold).update(
            user=buyer,
            coleccion_usuario=existing,
        )
        recalculate_progress(existing.id)
        publication.coleccion_usuario = existing
        publication.save(update_fields=["coleccion_usuario"])
        sold.delete()
    else:
        sold.user = buyer
        sold.save(update_fields=["user"])
        PiezaInventario.objects.filter(coleccion_usuario=sold).update(user=buyer)

    if sold.coleccion.propietario_id == publication.vendedor_id:
        sold.coleccion.propietario = buyer
        sold.coleccion.save(update_fields=["propietario"])


@transaction.atomic
def complete_offer(offer_id, user):
    offer = _lock_offer(offer_id)
    _require_seller(offer, user)
    publication = PublicacionMarket.objects.select_for_update().get(
        pk=offer.publicacion_id
    )
    if offer.estado != "ACEPTADA" or publication.estado != "RESERVADA":
        raise Conflict("La oferta no está lista para completarse.")

    resource_name = marketplace_resource_name(offer.publicacion)
    if publication.pieza_inventario_id:
        _transfer_piece(publication, offer.comprador)
    else:
        _transfer_collection(publication, offer.comprador)

    offer.estado = "COMPLETADA"
    offer.save(update_fields=["estado"])
    publication.estado = "VENDIDA"
    publication.save(update_fields=["estado"])
    notification_metadata = _offer_notification_metadata(offer, resource_name)
    notify(
        offer.comprador,
        "venta",
        f"La compra de {resource_name} se completó correctamente.",
        evento="SALE_COMPLETED_BUYER",
        destino_tipo="MARKETPLACE_PUBLICATION",
        destino_id=publication.id,
        metadata=notification_metadata,
    )
    notify(
        publication.vendedor,
        "venta",
        f"La venta de {resource_name} se completó correctamente.",
        evento="SALE_COMPLETED_SELLER",
        destino_tipo="MARKETPLACE_PUBLICATION",
        destino_id=publication.id,
        metadata=notification_metadata,
    )
    return offer
