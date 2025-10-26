import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SECRET_KEY = "test-secret-key"
DEBUG = True

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "reporting",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(BASE_DIR / "test.sqlite3"),
    }
}

USE_TZ = True
TIME_ZONE = "UTC"

MEDIA_ROOT = str(BASE_DIR / "media_test")
os.makedirs(MEDIA_ROOT, exist_ok=True)

ROOT_URLCONF = "proj.urls"
