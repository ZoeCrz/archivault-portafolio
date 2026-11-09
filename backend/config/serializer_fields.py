from rest_framework import serializers

from .media import resolve_media_url
from .validators import validate_image_file


class MediaFileField(serializers.FileField):
    """Writable FileField with the same URL representation used by GraphQL."""

    def __init__(self, *args, **kwargs):
        validators = list(kwargs.pop("validators", []))
        if validate_image_file not in validators:
            validators.append(validate_image_file)
        super().__init__(*args, validators=validators, **kwargs)

    def to_representation(self, value):
        request = self.context.get("request")
        return resolve_media_url(value, request=request)
