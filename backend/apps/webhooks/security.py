import hashlib
import hmac
import time

from django.conf import settings
from rest_framework.exceptions import APIException


class WebhookAuthenticationFailed(APIException):
    status_code = 401
    default_detail = "No se pudo autenticar la solicitud del webhook."
    default_code = "invalid_webhook_signature"


class WebhookConfigurationError(APIException):
    status_code = 500
    default_detail = "No se pudo procesar el webhook."
    default_code = "webhook_configuration_error"


def verify_webhook_signature(request):
    if not settings.WEBHOOK_SECRET:
        raise WebhookConfigurationError()

    timestamp = request.headers.get("X-ArchiVault-Timestamp", "")
    signature = request.headers.get("X-ArchiVault-Signature", "")
    delivery_id = request.headers.get("X-ArchiVault-Delivery", "")
    if not timestamp or not signature or not delivery_id:
        raise WebhookAuthenticationFailed()
    if len(delivery_id) > 120:
        raise WebhookAuthenticationFailed()

    try:
        timestamp_value = int(timestamp)
    except ValueError as exc:
        raise WebhookAuthenticationFailed() from exc

    if abs(int(time.time()) - timestamp_value) > settings.WEBHOOK_TOLERANCE_SECONDS:
        raise WebhookAuthenticationFailed()

    signed_payload = timestamp.encode() + b"." + request.body
    expected = hmac.new(
        settings.WEBHOOK_SECRET.encode(),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()
    supplied = signature.removeprefix("sha256=")
    if not hmac.compare_digest(expected, supplied):
        raise WebhookAuthenticationFailed()
    return delivery_id
