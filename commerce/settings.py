"""
Django settings for commerce project (Koyeb + Supabase).
Complete, production-ready defaults with local dev fallbacks.
"""

import os
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv

# Load local .env (if present). In production (Koyeb) env vars come from the platform.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# -------------------------
# Basic settings
# -------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "unsafe-secret-key")
DEBUG = os.environ.get("DJANGO_DEBUG", "False").lower() in ("1", "true", "yes")

# -------------------------
# Helpers
# -------------------------
def _split_env(name, default=""):
    raw = os.environ.get(name, default)
    if not raw:
        return []
    return [p.strip() for p in raw.split(",") if p.strip()]

# -------------------------
# Hosts and CSRF
# -------------------------
# Default includes localhost for local dev; override via env in production.
ALLOWED_HOSTS = _split_env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,auction.koyeb.app")

# CSRF_TRUSTED_ORIGINS must include scheme in Django 4+
_raw_csrf = _split_env("DJANGO_CSRF_TRUSTED_ORIGINS", "https://auction.koyeb.app")
CSRF_TRUSTED_ORIGINS = []
for entry in _raw_csrf:
    if entry.startswith("http://") or entry.startswith("https://"):
        CSRF_TRUSTED_ORIGINS.append(entry)
    else:
        CSRF_TRUSTED_ORIGINS.append("https://" + entry)

# -------------------------
# Installed apps & middleware
# -------------------------
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
        "DIRS": [os.path.join(BASE_DIR, "templates")],
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

# -------------------------
# Database configuration
# -------------------------
# Supports: local sqlite (for dev/dumpdata) and remote Postgres (Supabase) with SSL.
_db_url = os.environ.get("DATABASE_URL", "")

if _db_url and _db_url.startswith("sqlite"):
    # Local sqlite (use dj_database_url.parse to handle sqlite://... strings)
    DATABASES = {"default": dj_database_url.parse(_db_url)}
elif _db_url:
    # Remote Postgres (Supabase) — require SSL
    DATABASES = {
        "default": dj_database_url.config(
            default=_db_url,
            conn_max_age=int(os.environ.get("DJANGO_DB_CONN_MAX_AGE", 600)),
            ssl_require=True,
        )
    }
else:
    # Fallback to a local sqlite file if DATABASE_URL is not set
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
        }
    }

# -------------------------
# Proxy / SSL header (Koyeb)
# -------------------------
# Koyeb (and many platforms) set X-Forwarded-Proto; tell Django to trust it.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# -------------------------
# Security settings
# -------------------------
if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", 60))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
else:
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_SSL_REDIRECT = False

# -------------------------
# Auth
# -------------------------
AUTH_USER_MODEL = "auctions.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# -------------------------
# Internationalization
# -------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# -------------------------
# Static files (WhiteNoise)
# -------------------------
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# -------------------------
# Email
# -------------------------
EMAIL_BACKEND = os.environ.get("DJANGO_EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "no-reply@yourdomain.com")

# -------------------------
# Logging
# -------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False}
    },
}

# -------------------------
# Misc / optional settings
# -------------------------
# Allow file uploads size limit (example)
DATA_UPLOAD_MAX_MEMORY_SIZE = int(os.environ.get("DATA_UPLOAD_MAX_MEMORY_SIZE", 2621440))  # 2.5MB

# Any additional app-specific settings can go here
