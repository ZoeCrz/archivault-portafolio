from urllib.parse import urlsplit

from django.conf import settings


def resolve_media_url(value, request=None):
    """Return one canonical URL for a FileField value or historical URL."""
    if not value:
        return None

    if hasattr(value, "url"):
        try:
            raw_url = value.url
        except ValueError:
            return None
    else:
        raw_url = str(value).strip()

    if not raw_url:
        return None

    parsed = urlsplit(raw_url)
    if parsed.scheme in {"http", "https"}:
        return raw_url

    if parsed.scheme or raw_url.startswith("//"):
        return None

    if not raw_url.startswith("/"):
        media_prefix = settings.MEDIA_URL.rstrip("/")
        raw_url = f"{media_prefix}/{raw_url.lstrip('/')}"

    if request is not None:
        return request.build_absolute_uri(raw_url)
    return raw_url
