from decimal import Decimal

from django.db import migrations


def recalculate_progress(apps, schema_editor):
    ColeccionUsuario = apps.get_model("catalog", "ColeccionUsuario")
    PiezaInventario = apps.get_model("catalog", "PiezaInventario")

    for participation in ColeccionUsuario.objects.select_related("coleccion").iterator():
        total = participation.coleccion.total_piezas
        if total <= 0:
            progress = Decimal("0.00")
        else:
            acquired = PiezaInventario.objects.filter(
                coleccion_usuario_id=participation.id
            ).values("pieza_catalogo_id").distinct().count()
            progress = min(
                Decimal(acquired) * Decimal("100") / Decimal(total),
                Decimal("100"),
            ).quantize(Decimal("0.01"))
        ColeccionUsuario.objects.filter(pk=participation.id).update(progreso=progress)


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0003_coleccionmaestra_imagen_piezafoto_archivo_and_more"),
    ]

    operations = [
        migrations.RunPython(recalculate_progress, migrations.RunPython.noop),
    ]
