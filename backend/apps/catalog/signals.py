from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from .models import ColeccionMaestra, PiezaInventario
from .progress import recalculate_collection_progress, recalculate_progress


@receiver(pre_save, sender=PiezaInventario)
def remember_previous_participation(sender, instance, **kwargs):
    if not instance.pk:
        instance._previous_participation_id = None
        return
    instance._previous_participation_id = sender.objects.filter(pk=instance.pk).values_list(
        "coleccion_usuario_id", flat=True
    ).first()


@receiver(post_save, sender=PiezaInventario)
def update_progress_after_piece_save(sender, instance, **kwargs):
    previous_id = getattr(instance, "_previous_participation_id", None)
    if previous_id and previous_id != instance.coleccion_usuario_id:
        recalculate_progress(previous_id)
    recalculate_progress(instance.coleccion_usuario_id)


@receiver(post_delete, sender=PiezaInventario)
def update_progress_after_piece_delete(sender, instance, **kwargs):
    recalculate_progress(instance.coleccion_usuario_id)


@receiver(post_save, sender=ColeccionMaestra)
def update_progress_after_collection_save(sender, instance, **kwargs):
    recalculate_collection_progress(instance.id)
