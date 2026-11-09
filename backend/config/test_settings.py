"""Isolated test environment. Never use for deployment."""
import os
os.environ['DEBUG'] = 'True'
os.environ.setdefault('SECRET_KEY', 'test-only-' * 8)
os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')
from .settings import *  # noqa: F403
REST_FRAMEWORK = {**REST_FRAMEWORK, 'DEFAULT_THROTTLE_CLASSES': (),
                 'DEFAULT_THROTTLE_RATES': {'anon': None, 'user': None, 'authentication': None}}
SECURE_SSL_REDIRECT = False
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
