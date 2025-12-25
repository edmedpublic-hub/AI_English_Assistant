from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-temp-key"
DEBUG = True

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'corsheaders',
    'django_extensions',

    # Local apps
    'content',
    'reading',
    'vocab_master',
    'translation',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

# -------------------------
#      TEMPLATE SETUP
# -------------------------
# IMPORTANT: This now points to your global /templates folder
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates'
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# -------------------------
#      STATIC FILES
# -------------------------
STATIC_URL = '/static/'

# These are YOUR actual static files (JS/CSS)
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Where collectstatic dumps files
STATIC_ROOT = BASE_DIR / "staticfiles"

# -------------------------
#      CORS
# -------------------------
CORS_ALLOW_ALL_ORIGINS = True

# -------------------------
#      OPENAI
# -------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
