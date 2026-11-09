from django.contrib.auth import get_user_model
from django.db.models import Case, CharField, Count, F, IntegerField, OuterRef, Subquery, Value, When
from django.db.models.functions import Coalesce

from apps.marketplace.services import marketplace_name_expression, visible_publications_for


MAX_COMMUNITY_INSIGHTS = 5


def _bounded_limit(limit):
    return max(0, min(int(limit), MAX_COMMUNITY_INSIGHTS))


def latest_marketplace_publications(user, limit=MAX_COMMUNITY_INSIGHTS):
    """Newest visible and available listings with a user-facing name."""
    return (
        visible_publications_for(user)
        .filter(estado__in=["ACTIVA", "RESERVADA"])
        .select_related(
            "pieza_inventario__pieza_catalogo",
            "coleccion_usuario__coleccion",
        )
        .annotate(
            insight_tipo=Case(
                When(pieza_inventario__isnull=False, then=Value("PIEZA")),
                default=Value("COLECCION"),
                output_field=CharField(),
            ),
            insight_nombre=marketplace_name_expression(),
        )
        .order_by("-fecha_publicacion", "-id")[: _bounded_limit(limit)]
    )


def top_collectors(limit=MAX_COMMUNITY_INSIGHTS):
    """Rank authors by non-self likes and comments received across all posts."""
    from .models import Comentario, PostLike

    like_totals = (
        PostLike.objects.filter(post__user_id=OuterRef("pk"))
        .exclude(user_id=OuterRef("pk"))
        .values("post__user_id")
        .annotate(total=Count("id"))
        .values("total")
    )
    comment_totals = (
        Comentario.objects.filter(post__user_id=OuterRef("pk"))
        .exclude(user_id=OuterRef("pk"))
        .values("post__user_id")
        .annotate(total=Count("id"))
        .values("total")
    )
    return (
        get_user_model()
        .objects.annotate(
            likes_recibidos=Coalesce(
                Subquery(like_totals, output_field=IntegerField()),
                Value(0),
            ),
            comentarios_recibidos=Coalesce(
                Subquery(comment_totals, output_field=IntegerField()),
                Value(0),
            ),
        )
        .annotate(score=F("likes_recibidos") + F("comentarios_recibidos"))
        .filter(score__gt=0)
        .order_by("-score", "id")[: _bounded_limit(limit)]
    )
