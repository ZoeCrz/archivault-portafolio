from django.db import migrations, models
from django.db.models import Count


def ensure_favorites_are_unique(apps, schema_editor):
    Favorito = apps.get_model("catalog", "Favorito")
    duplicate_piece = (
        Favorito.objects.exclude(pieza_inventario_id=None)
        .values("user_id", "pieza_inventario_id")
        .annotate(total=Count("id"))
        .filter(total__gt=1)
        .order_by("user_id", "pieza_inventario_id")
        .first()
    )
    duplicate_collection = (
        Favorito.objects.exclude(coleccion_maestra_id=None)
        .values("user_id", "coleccion_maestra_id")
        .annotate(total=Count("id"))
        .filter(total__gt=1)
        .order_by("user_id", "coleccion_maestra_id")
        .first()
    )
    if duplicate_piece or duplicate_collection:
        raise RuntimeError(
            "No se puede aplicar la unicidad de favoritos porque existen "
            "favoritos duplicados. Revisa los registros antes de continuar."
        )


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0006_favorite_collections"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="favorito",
            name="unique_user_piece_favorite",
        ),
        migrations.RemoveConstraint(
            model_name="favorito",
            name="unique_user_master_collection_favorite",
        ),
        migrations.RunPython(ensure_favorites_are_unique, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="favorito",
            constraint=models.UniqueConstraint(
                fields=("user", "pieza_inventario"),
                name="unique_user_piece_favorite",
            ),
        ),
        migrations.AddConstraint(
            model_name="favorito",
            constraint=models.UniqueConstraint(
                fields=("user", "coleccion_maestra"),
                name="unique_user_master_collection_favorite",
            ),
        ),
    ]
