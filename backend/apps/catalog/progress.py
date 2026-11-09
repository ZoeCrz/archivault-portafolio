from decimal import Decimal

from .models import ColeccionUsuario, PiezaInventario


def calculate_progress(participation):
    total = participation.coleccion.total_piezas
    if total <= 0:
        return Decimal("0.00")

    acquired = PiezaInventario.objects.filter(
        coleccion_usuario=participation
    ).values("pieza_catalogo_id").distinct().count()
    percentage = min(Decimal(acquired) * Decimal("100") / Decimal(total), Decimal("100"))
    return percentage.quantize(Decimal("0.01"))


def recalculate_progress(participation_id):
    participation = ColeccionUsuario.objects.select_related("coleccion").filter(
        pk=participation_id
    ).first()
    if participation is None:
        return

    progress = calculate_progress(participation)
    ColeccionUsuario.objects.filter(pk=participation_id).update(progreso=progress)


def recalculate_collection_progress(collection_id):
    participation_ids = ColeccionUsuario.objects.filter(
        coleccion_id=collection_id
    ).values_list("id", flat=True)
    for participation_id in participation_ids.iterator():
        recalculate_progress(participation_id)
