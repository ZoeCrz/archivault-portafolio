from django.core.exceptions import ValidationError
from PIL import Image, UnidentifiedImageError

MAX_IMAGE_SIZE = 5 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP", "GIF"}


def validate_image_file(file):
    if file.size > MAX_IMAGE_SIZE:
        raise ValidationError("La imagen no puede superar 5 MB.")
    content_type = getattr(file, "content_type", None)
    if content_type and content_type not in ALLOWED_IMAGE_TYPES:
        raise ValidationError("Formato no permitido. Usa JPEG, PNG, WEBP o GIF.")
    position = file.tell()
    try:
        file.seek(0)
        with Image.open(file) as image:
            if image.format not in ALLOWED_FORMATS or image.width * image.height > 20_000_000:
                raise ValidationError("Formato o dimensiones de imagen no permitidos.")
            image.verify()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as error:
        raise ValidationError("El archivo no contiene una imagen válida.") from error
    finally:
        file.seek(position)
