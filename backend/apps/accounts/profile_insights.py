from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.catalog.models import ColeccionUsuario, PiezaInventario
from apps.community.models import PostLike
from apps.marketplace.models import PublicacionMarket
from apps.marketplace.services import marketplace_resource_name
from .models import Profile, Resena


OWNER_ACTIVITY_TYPES = {
    "likes_realizados", "likes_recibidos", "ventas", "resenas_hechas", "resenas_recibidas"
}
PUBLIC_ACTIVITY_TYPES = {"likes_recibidos", "resenas_recibidas"}


def accessible_profiles_for(user):
    return Profile.objects.filter(Q(user=user) | Q(perfil_publico=True)).select_related("user")


def get_accessible_profile(user, profile_id):
    return get_object_or_404(accessible_profiles_for(user), pk=profile_id)


def _review_stats(user_id):
    reviews = Resena.objects.filter(receptor_id=user_id)
    aggregate = reviews.aggregate(
        cantidad=Count("id"), promedio=Avg("puntuacion")
    )
    distribution = {str(score): 0 for score in range(1, 6)}
    for row in reviews.values("puntuacion").annotate(total=Count("id")):
        distribution[str(row["puntuacion"])] = row["total"]
    return aggregate, distribution


def build_profile_summary(profile, request):
    owner = profile.user_id == request.user.id
    user_id = profile.user_id
    inventory = PiezaInventario.objects.filter(user_id=user_id)
    visible_inventory = inventory if owner else inventory.filter(visibilidad="PUBLICA")
    collection_rows = (
        ColeccionUsuario.objects.filter(user_id=user_id)
        .select_related("coleccion")
        .annotate(
            piece_count=Count("piezainventario"),
            public_piece_count=Count("piezainventario", filter=Q(piezainventario__visibilidad="PUBLICA")),
        )
    )
    if not owner:
        collection_rows = collection_rows.filter(public_piece_count__gt=0)
    collection_count = collection_rows.count()
    collection_rows = list(collection_rows.order_by("id")[:5])

    likes_received = PostLike.objects.filter(post__user_id=user_id).exclude(user_id=user_id).count()
    likes_made = PostLike.objects.filter(user_id=user_id).count() if owner else None
    sales = PublicacionMarket.objects.filter(
        vendedor_id=user_id, estado="VENDIDA", oferta__estado="COMPLETADA"
    ).distinct().count()
    review_stats, review_distribution = _review_stats(user_id)
    reviews_received = list(
        Resena.objects.filter(receptor_id=user_id).select_related("emisor").order_by("-id")[:5]
    )

    from config.media import resolve_media_url
    profile_data = {
        "id": profile.id,
        "user": {"id": user_id, "nombre": profile.user.username},
        "avatar": resolve_media_url(profile.avatar, request=request),
        "biografia": profile.biografia,
        "ubicacion": profile.ubicacion,
        "perfil_publico": profile.perfil_publico,
        "fecha_registro": profile.fecha_registro.isoformat(),
    }
    stats = {
        "piezas_registradas" if owner else "piezas_publicas": visible_inventory.count(),
        "colecciones": collection_count,
        "likes_recibidos": likes_received,
        "ventas_completadas": sales,
        "promedio_resenas": float(review_stats["promedio"]) if review_stats["promedio"] is not None else None,
        "cantidad_resenas": review_stats["cantidad"],
    }
    if owner:
        stats["likes_realizados"] = likes_made

    result = {
        "profile": profile_data,
        "is_owner": owner,
        "estadisticas": stats,
        "colecciones": {
            "count": stats["colecciones"],
            "results": [
                {
                    "id": row.coleccion_id,
                    "coleccion_usuario_id": row.id if owner else None,
                    "nombre": row.coleccion.nombre,
                    "piezas": row.piece_count if owner else row.public_piece_count,
                    "progreso": float(row.progreso) if owner else None,
                }
                for row in collection_rows
            ],
        },
        "likes": {"recibidos": {"count": likes_received}},
        "ventas": {"count": sales},
        "resenas": {
            "recibidas": {
                "count": review_stats["cantidad"],
                "results": [
                    {"id": item.id, "autor": {"id": item.emisor_id, "nombre": item.emisor.username}, "puntuacion": item.puntuacion, "comentario": item.comentario}
                    for item in reviews_received
                ],
            }
        },
    }
    if owner:
        result["likes"]["realizados"] = {"count": likes_made}
        result["resenas"]["hechas"] = {"count": Resena.objects.filter(emisor_id=user_id).count()}
        inventory_distribution = {"ADQUIRIDA": 0, "DESEADA": 0}
        for row in inventory.values("estado_adquisicion").annotate(total=Count("id")):
            if row["estado_adquisicion"] in inventory_distribution:
                inventory_distribution[row["estado_adquisicion"]] = row["total"]
        result["distribuciones"] = {
            "inventario_por_estado": inventory_distribution,
            "resenas_por_puntuacion": review_distribution,
        }
    return result


def profile_activity_queryset(profile, viewer, activity_type):
    owner = profile.user_id == viewer.id
    allowed = OWNER_ACTIVITY_TYPES if owner else PUBLIC_ACTIVITY_TYPES
    if activity_type not in OWNER_ACTIVITY_TYPES:
        raise ValidationError({"tipo": ["Selecciona un tipo de actividad válido."]})
    if activity_type not in allowed:
        raise PermissionDenied("No tienes permiso para consultar esta actividad.")
    user_id = profile.user_id
    if activity_type == "likes_realizados":
        return PostLike.objects.filter(user_id=user_id).select_related("post__user").order_by("-id")
    if activity_type == "likes_recibidos":
        return PostLike.objects.filter(post__user_id=user_id).exclude(user_id=user_id).select_related("user", "post").order_by("-id")
    if activity_type == "ventas":
        return PublicacionMarket.objects.filter(vendedor_id=user_id, estado="VENDIDA", oferta__estado="COMPLETADA").select_related("pieza_inventario__pieza_catalogo", "coleccion_usuario__coleccion").distinct().order_by("-id")
    if activity_type == "resenas_hechas":
        return Resena.objects.filter(emisor_id=user_id).select_related("receptor").order_by("-id")
    return Resena.objects.filter(receptor_id=user_id).select_related("emisor").order_by("-id")


def serialize_profile_activity(items, activity_type):
    if activity_type.startswith("likes_"):
        received = activity_type == "likes_recibidos"
        return [{
            "id": item.id,
            "post_id": item.post_id,
            "post_contenido": item.post.contenido,
            "usuario": {"id": item.user_id if received else item.post.user_id, "nombre": item.user.username if received else item.post.user.username},
        } for item in items]
    if activity_type == "ventas":
        return [{"id": item.id, "nombre": marketplace_resource_name(item), "tipo": "PIEZA" if item.pieza_inventario_id else "COLECCION", "estado": item.estado, "precio": str(item.precio)} for item in items]
    made = activity_type == "resenas_hechas"
    return [{
        "id": item.id,
        "usuario": {"id": item.receptor_id if made else item.emisor_id, "nombre": item.receptor.username if made else item.emisor.username},
        "puntuacion": item.puntuacion,
        "comentario": item.comentario,
    } for item in items]
