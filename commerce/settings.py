"""
Django settings for commerce project (Koyeb + Supabase).
"""

import os
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv

# Load local .env (if present). This makes running locally simple.
# In production (Koyeb) environment variables will come from the platform.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Defaults and safety
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "unsafe-secret-key")
DEBUG = os.environ.get("DJANGO_DEBUG", "False").lower() in ("1", "true", "yes")

# Helper to split comma-separated env vars into a list, ignoring empties
def _split_env(name, default=""):
    raw = os.environ.get(name, default)
    if not raw:
        return []
    return [p.strip() for p in raw.split(",") if p.strip()]

# ALLOWED_HOSTS: default to localhost for local dev
ALLOWED_HOSTS = _split_env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")

# CSRF_TRUSTED_ORIGINS must include scheme in Django 4+
_raw_csrf = _split_env("DJANGO_CSRF_TRUSTED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS = []
for entry in _raw_csrf:
    if entry.startswith("http://") or entry.startswith("https://"):
        CSRF_TRUSTED_ORIGINS.append(entry)
    else:
        CSRF_TRUSTED_ORIGINS.append("https://" + entry)

INSTALLED_APPS = [
    "auctions",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "commerce.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "auctions.context_processors.notifications_count",
            ],
        },
    },
]

WSGI_APPLICATION = "commerce.wsgi.application"

# Database: parse DATABASE_URL; require SSL for Supabase
DATABASES = {
    "default": dj_database_url.config(
        default=os.environ.get("DATABASE_URL"),
        conn_max_age=int(os.environ.get("DJANGO_DB_CONN_MAX_AGE", 600)),
        ssl_require=True,
    )
}

AUTH_USER_MODEL = "auctions.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Auth redirects
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# Email
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "no-reply@yourdomain.com"

# Minimal logging to surface errors in Koyeb logs
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False}
    },
}
