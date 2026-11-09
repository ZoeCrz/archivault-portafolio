import json

from .models import Notificacion


ALLOWED_METADATA_KEYS = {
    "actor_id",
    "actor_name",
    "resource_type",
    "resource_name",
    "offer_id",
    "amount",
}


def _normalize_metadata(metadata):
    if metadata is None:
        return {}
    if not isinstance(metadata, dict):
        raise ValueError("Los metadatos de la notificación deben ser un objeto.")
    unknown = set(metadata) - ALLOWED_METADATA_KEYS
    if unknown:
        raise ValueError("Los metadatos contienen campos no permitidos.")
    normalized = {
        key: value
        for key, value in metadata.items()
        if value is not None
    }
    try:
        json.dumps(normalized)
    except (TypeError, ValueError) as exc:
        raise ValueError("Los metadatos deben contener valores serializables.") from exc
    return normalized


def notify(
    user,
    tipo,
    mensaje,
    *,
    evento="GENERAL",
    destino_tipo=None,
    destino_id=None,
    metadata=None,
):
    if user is None:
        return None
    if (destino_tipo is None) != (destino_id is None):
        raise ValueError("El tipo y el identificador de destino deben proporcionarse juntos.")
    valid_destinations = {choice[0] for choice in Notificacion.DESTINOS}
    if destino_tipo is not None and destino_tipo not in valid_destinations:
        raise ValueError("El tipo de destino no está permitido.")
    valid_events = {choice[0] for choice in Notificacion.EVENTOS}
    if evento not in valid_events:
        raise ValueError("El evento de notificación no está permitido.")
    return Notificacion.objects.create(
        user=user,
        tipo=tipo,
        mensaje=mensaje,
        evento=evento,
        destino_tipo=destino_tipo,
        destino_id=destino_id,
        metadata=_normalize_metadata(metadata),
    )
