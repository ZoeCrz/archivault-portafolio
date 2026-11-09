import environ
from django.core.exceptions import ImproperlyConfigured
from pathlib import Path

from config.storage import build_media_storage_config

BASE_DIR = Path(__file__).resolve().parent.parent
env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / ".env")

DEBUG = env("DEBUG")
SECRET_KEY = env("SECRET_KEY", default="")
if not SECRET_KEY or SECRET_KEY.startswith(('replace-', 'dev-insecure')) or len(SECRET_KEY) < 50:
    raise ImproperlyConfigured('Configure SECRET_KEY with at least 50 random characters.')
WEBHOOK_SECRET = env("WEBHOOK_SECRET", default="")
WEBHOOK_TOLERANCE_SECONDS = env.int("WEBHOOK_TOLERANCE_SECONDS", default=300)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
if not DEBUG and '*' in ALLOWED_HOSTS:
    raise ImproperlyConfigured('Production ALLOWED_HOSTS must not include a wildcard.')
CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=[]
)

# These headers must only be trusted when requests always pass through a
# controlled reverse proxy that overwrites them.
if env.bool("TRUST_X_FORWARDED_PROTO", default=False):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = env.bool("USE_X_FORWARDED_HOST", default=False)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Terceros
    "rest_framework",
    "corsheaders",
    "graphene_django",
    # Apps del proyecto (las activa tu compañero en Fase 3):
     "apps.accounts",
     "apps.catalog",
     "apps.marketplace",
     "apps.community",
     "apps.webhooks",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# Por defecto SQLite (para probar sin BD). En Fase 2 defines DATABASE_URL=mysql://...
DATABASES = {
    "default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
}

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=["http://localhost:5173"])

REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_CLASSES": ('rest_framework.throttling.AnonRateThrottle', 'rest_framework.throttling.UserRateThrottle'),
    "DEFAULT_THROTTLE_RATES": {'anon': '100/hour', 'user': '1000/hour', 'authentication': '10/min'},
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "EXCEPTION_HANDLER": "config.exceptions.api_exception_handler",
}

GRAPHENE = {"SCHEMA": "config.schema.schema"}

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
STORAGES = {
    "default": build_media_storage_config(
        env("MEDIA_STORAGE_BACKEND", default="filesystem"),
        bucket_name=env("AWS_STORAGE_BUCKET_NAME", default=""),
        region_name=env("AWS_S3_REGION_NAME", default=""),
        querystring_expire=env("AWS_S3_QUERYSTRING_EXPIRE", default="900"),
    ),
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LANGUAGE_CODE = "es-mx"
TIME_ZONE = "America/Mexico_City"
USE_I18N = True
USE_TZ = True
CORS_ALLOW_ALL_ORIGINS = False
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
SIMPLE_JWT = {'CHECK_REVOKE_TOKEN': True}
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = not DEBUG
