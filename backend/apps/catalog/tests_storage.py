from urllib.parse import parse_qs, urlsplit

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import FileSystemStorage
from django.test import RequestFactory, SimpleTestCase, override_settings
from storages.backends.s3 import S3Storage

from apps.accounts.models import Profile
from apps.community.models import Comentario, PostMedia
from config.media import resolve_media_url
from config.serializer_fields import MediaFileField
from config.storage import (
    FILESYSTEM_STORAGE_BACKEND,
    S3_STORAGE_BACKEND,
    build_media_storage_config,
)
from .models import ColeccionMaestra, PiezaFoto


class MediaStorageConfigurationTests(SimpleTestCase):
    def test_local_storage_is_the_default(self):
        self.assertEqual(
            build_media_storage_config(),
            {"BACKEND": FILESYSTEM_STORAGE_BACKEND},
        )
        self.assertEqual(settings.STORAGES["default"]["BACKEND"], FILESYSTEM_STORAGE_BACKEND)
        self.assertIsInstance(FileSystemStorage(), FileSystemStorage)

    def test_s3_is_selected_only_explicitly_and_is_private(self):
        config = build_media_storage_config(
            "s3",
            bucket_name="archivault-test-media",
            region_name="us-east-1",
            querystring_expire="300",
        )

        self.assertEqual(config["BACKEND"], S3_STORAGE_BACKEND)
        self.assertEqual(
            config["OPTIONS"],
            {
                "bucket_name": "archivault-test-media",
                "region_name": "us-east-1",
                "default_acl": None,
                "querystring_auth": True,
                "querystring_expire": 300,
                "signature_version": "s3v4",
                "file_overwrite": False,
            },
        )
        self.assertNotIn("access_key", config["OPTIONS"])
        self.assertNotIn("secret_key", config["OPTIONS"])

    def test_s3_requires_bucket_and_region(self):
        for bucket_name, region_name, expected in (
            ("", "us-east-1", "AWS_STORAGE_BUCKET_NAME"),
            ("media", "", "AWS_S3_REGION_NAME"),
        ):
            with self.subTest(expected=expected):
                with self.assertRaisesMessage(ImproperlyConfigured, expected):
                    build_media_storage_config(
                        "s3", bucket_name=bucket_name, region_name=region_name
                    )

    def test_rejects_unknown_backend_and_invalid_expiry(self):
        with self.assertRaises(ImproperlyConfigured):
            build_media_storage_config("unknown")
        with self.assertRaises(ImproperlyConfigured):
            build_media_storage_config(
                "s3",
                bucket_name="media",
                region_name="us-east-1",
                querystring_expire=0,
            )


class S3MediaContractTests(SimpleTestCase):
    def setUp(self):
        # Dummy credentials only prevent boto3 from consulting external
        # credential providers; URL signing is entirely local in this test.
        self.storage = S3Storage(
            bucket_name="archivault-test-media",
            region_name="us-east-1",
            default_acl=None,
            querystring_auth=True,
            querystring_expire=300,
            signature_version="s3v4",
            file_overwrite=False,
            access_key="test-access-key",
            secret_key="test-secret-key",
        )

    def test_private_s3_url_is_signed_without_contacting_aws(self):
        url = self.storage.url("pieces/item.png")
        parsed = urlsplit(url)
        query = parse_qs(parsed.query)

        self.assertEqual(parsed.scheme, "https")
        self.assertIn("archivault-test-media", parsed.netloc)
        self.assertEqual(parsed.path, "/pieces/item.png")
        self.assertIn("X-Amz-Signature", query)
        self.assertEqual(query["X-Amz-Expires"], ["300"])

    @override_settings(ALLOWED_HOSTS=["api.example"])
    def test_serializer_preserves_signed_and_historical_absolute_urls(self):
        signed_url = self.storage.url("profiles/avatars/avatar.png")
        historical_url = "https://legacy.example/avatar.png"
        request = RequestFactory().get("/", secure=True, HTTP_HOST="api.example")
        field = MediaFileField()
        field._context = {"request": request}

        class StoredValue:
            def __init__(self, url):
                self.url = url

        self.assertEqual(field.to_representation(StoredValue(signed_url)), signed_url)
        self.assertEqual(resolve_media_url(historical_url, request), historical_url)

    def test_existing_file_fields_keep_their_upload_paths(self):
        expected_paths = (
            (Profile, "avatar", "profiles/avatars/"),
            (ColeccionMaestra, "imagen", "collections/"),
            (PiezaFoto, "archivo", "pieces/"),
            (PostMedia, "archivo", "community/posts/"),
            (Comentario, "imagen", "community/comments/"),
        )

        for model, field_name, upload_to in expected_paths:
            with self.subTest(model=model.__name__, field=field_name):
                self.assertEqual(model._meta.get_field(field_name).upload_to, upload_to)
