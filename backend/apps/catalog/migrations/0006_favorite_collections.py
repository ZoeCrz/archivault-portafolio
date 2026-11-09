# Generated manually for the polymorphic (piece/master collection) favorite contract.
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """
    Existing piece favorites keep their primary key, user and piece unchanged.

    A reverse migration is safe while no collection favorite exists. Once collection
    favorites have been created, operators must remove or export those rows before
    rolling back because the previous schema cannot represent them. The migration
    intentionally performs no destructive automatic rollback.
    """

    dependencies = [
        ("catalog", "0005_alter_piezainventario_condicion_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="favorito",
            name="pieza_inventario",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="favoritos",
                to="catalog.piezainventario",
            ),
        ),
        migrations.AddField(
            model_name="favorito",
            name="coleccion_maestra",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="favoritos",
                to="catalog.coleccionmaestra",
            ),
        ),
        migrations.RemoveConstraint(
            model_name="favorito",
            name="unique_user_inventory_favorite",
        ),
        migrations.AddConstraint(
            model_name="favorito",
            constraint=models.CheckConstraint(
                check=(
                    models.Q(
                        pieza_inventario__isnull=False,
                        coleccion_maestra__isnull=True,
                    )
                    | models.Q(
                        pieza_inventario__isnull=True,
                        coleccion_maestra__isnull=False,
                    )
                ),
                name="favorite_exactly_one_target",
            ),
        ),
        migrations.AddConstraint(
            model_name="favorito",
            constraint=models.UniqueConstraint(
                condition=models.Q(pieza_inventario__isnull=False),
                fields=("user", "pieza_inventario"),
                name="unique_user_piece_favorite",
            ),
        ),
        migrations.AddConstraint(
            model_name="favorito",
            constraint=models.UniqueConstraint(
                condition=models.Q(coleccion_maestra__isnull=False),
                fields=("user", "coleccion_maestra"),
                name="unique_user_master_collection_favorite",
            ),
        ),
    ]
