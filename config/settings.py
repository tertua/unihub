"""
Django settings for Faculty Learning Hub.

Every deployment-specific value comes from the environment (.env), so the same
code runs locally, in CI and in production without edits.
"""

import os
import sys
from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

# Centralize bytecode in .cache/python (gitignored). The env var alone only
# reaches child processes, so mirror it for the current interpreter as well.
os.environ.setdefault("PYTHONPYCACHEPREFIX", str(BASE_DIR / ".cache" / "python"))
sys.pycache_prefix = os.environ["PYTHONPYCACHEPREFIX"]

environ.Env.read_env(BASE_DIR / ".env")

env = environ.Env(DEBUG=(bool, False), ALLOWED_HOSTS=(list, []))

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "drf_spectacular",
    # Local apps
    "accounts",
    "materials",
    "tools",
    "chat",
    "spaces",
]

MIDDLEWARE = [
    # CORS must run first so preflight answers never hit auth/csrf middleware.
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

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

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# Database
# https://docs.djangoproject.com/en/stable/ref/settings/#databases
#
# PostgreSQL only, no SQLite fallback (see docs/adr/001-database-strategy.md).
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME", default="faculty_hub"),
        "USER": env("DB_USER", default="postgres"),
        "PASSWORD": env("DB_PASSWORD", default="postgres"),
        "HOST": env("DB_HOST", default="localhost"),
        "PORT": env("DB_PORT", default="5432"),
    }
}


# Google Drive integration — both optional; absence must never break the API.
GOOGLE_DRIVE_API_KEY = env("GOOGLE_DRIVE_API_KEY", default="")
GOOGLE_DRIVE_SERVICE_ACCOUNT_B64 = env("GOOGLE_DRIVE_SERVICE_ACCOUNT_B64", default="")
# Google Drive storage — service-account JSON (base64) + Shared Drive target.
# When the service account AND a folder/shared-drive id are present, uploads go
# to Google Drive; otherwise they stay on local disk (dev/test = zero network).
GOOGLE_DRIVE_SHARED_DRIVE_ID = env("GOOGLE_DRIVE_SHARED_DRIVE_ID", default="")
GOOGLE_DRIVE_FOLDER_ID = env("GOOGLE_DRIVE_FOLDER_ID", default="")


# Custom user model — must be declared before the first migration.
AUTH_USER_MODEL = "accounts.User"


# Password validation
# https://docs.djangoproject.com/en/stable/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/stable/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/stable/howto/static-files/

STATIC_URL = "static/"


# Media files (uploaded materials). Local disk only as the zero-network
# fallback; when Drive credentials + a target are set, uploads go to the Shared
# Drive (docs/adr/003-google-shared-drive-storage.md).
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Storage selection is credential-gated: unconfigured -> local disk (dev/test
# stay zero-network), configured -> the Drive backend writes to the Shared Drive.
_DRIVE_CREDS = GOOGLE_DRIVE_SERVICE_ACCOUNT_B64
_DRIVE_TARGET = GOOGLE_DRIVE_FOLDER_ID or GOOGLE_DRIVE_SHARED_DRIVE_ID

STORAGES = {
    "default": {
        "BACKEND": (
            "materials.storage.GoogleDriveStorage"
            if (_DRIVE_CREDS and _DRIVE_TARGET)
            else "django.core.files.storage.FileSystemStorage"
        ),
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Cache — explicit so the choice survives Django default changes (B4/D4).
# LocMemCache lives in this process only: a multi-worker deploy would need a
# shared backend (Redis/DB), which is out of scope for this batch.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "faculty-hub",
    },
}


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# CORS — the frontend dev server is a separate origin.
CORS_ALLOWED_ORIGINS = ["http://localhost:3000"]


# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}


# SimpleJWT — token lifetimes must match the cookie max-ages the webui writes
# (ACCESS_MAX_AGE / REFRESH_MAX_AGE in webui/src/lib/api-client.ts: 15 minutes
# for access, 7 days for refresh). These used to be the silent library defaults
# (5 minutes / 1 day), which made the cookie claims lie about refresh validity.
SIMPLEJWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}


# OpenAPI schema served at /api/schema/ and browsed at /api/docs/
SPECTACULAR_SETTINGS = {
    "TITLE": "Faculty Learning Hub API",
    "VERSION": "1.0.0",
}


# Test runs swap in the fast MD5 hasher: the default PBKDF2 costs ~2s per hash
# on dev hardware and dominated the suite (setUp creates three users per test).
# The hashing algorithm itself is not under test; production hashing is
# unchanged because this branch only fires for `manage.py test`.
if "test" in sys.argv:
    PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
