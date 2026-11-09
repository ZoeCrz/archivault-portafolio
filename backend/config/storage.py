from django.core.exceptions import ImproperlyConfigured


FILESYSTEM_STORAGE_BACKEND = "django.core.files.storage.FileSystemStorage"
S3_STORAGE_BACKEND = "storages.backends.s3.S3Storage"


def build_media_storage_config(
    backend="filesystem",
    *,
    bucket_name="",
    region_name="",
    querystring_expire=900,
):
    """Build the default storage config without resolving AWS credentials.

    Credentials are intentionally omitted so boto3 can use its standard
    credential chain, including an ECS task role when one is configured.
    """
    selected_backend = (backend or "filesystem").strip().lower()

    if selected_backend == "filesystem":
        return {"BACKEND": FILESYSTEM_STORAGE_BACKEND}

    if selected_backend != "s3":
        raise ImproperlyConfigured(
            "MEDIA_STORAGE_BACKEND debe ser 'filesystem' o 's3'."
        )

    missing_settings = []
    if not (bucket_name or "").strip():
        missing_settings.append("AWS_STORAGE_BUCKET_NAME")
    if not (region_name or "").strip():
        missing_settings.append("AWS_S3_REGION_NAME")
    if missing_settings:
        raise ImproperlyConfigured(
            "El almacenamiento S3 requiere: " + ", ".join(missing_settings)
        )

    try:
        signed_url_lifetime = int(querystring_expire)
    except (TypeError, ValueError) as exc:
        raise ImproperlyConfigured(
            "AWS_S3_QUERYSTRING_EXPIRE debe ser un entero positivo."
        ) from exc
    if signed_url_lifetime <= 0:
        raise ImproperlyConfigured(
            "AWS_S3_QUERYSTRING_EXPIRE debe ser un entero positivo."
        )

    return {
        "BACKEND": S3_STORAGE_BACKEND,
        "OPTIONS": {
            "bucket_name": bucket_name.strip(),
            "region_name": region_name.strip(),
            "default_acl": None,
            "querystring_auth": True,
            "querystring_expire": signed_url_lifetime,
            "signature_version": "s3v4",
            "file_overwrite": False,
        },
    }
