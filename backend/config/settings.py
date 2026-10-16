"""
Ustawienia Django dla Training Culture.

Wszystko, co różni się między komputerem a serwerem (Northflank), idzie przez
zmienne środowiskowe — patrz .env.example w katalogu głównym.
"""
import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
# Lokalnie zmienne z pliku .env w katalogu głównym. Na serwerze pliku nie ma (.dockerignore),
# a zmienne ustawione w środowisku i tak mają pierwszeństwo.
load_dotenv(BASE_DIR.parent / '.env')
# Statyczna strona (index.html, szkolenia.html, css, js, images)
PUBLIC_DIR = BASE_DIR.parent / 'public'


def env_list(name, default=''):
    return [item.strip() for item in os.environ.get(name, default).split(',') if item.strip()]


DEBUG = os.environ.get('DJANGO_DEBUG', '0') == '1'

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', '')
if not SECRET_KEY:
    if not DEBUG:
        raise RuntimeError('Ustaw zmienną DJANGO_SECRET_KEY (lub DJANGO_DEBUG=1 lokalnie).')
    SECRET_KEY = 'dev-only-insecure-key'

ALLOWED_HOSTS = env_list('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1')
CSRF_TRUSTED_ORIGINS = env_list('DJANGO_CSRF_TRUSTED_ORIGINS')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'ranking',
    'shop',
    'trainings',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'shop.context_processors.cart',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Lokalnie SQLite, na Northflanku Postgres z DATABASE_URL
DATABASES = {
    'default': dj_database_url.config(
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}',
        conn_max_age=600,
    )
}

AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'ranking:list'
LOGOUT_REDIRECT_URL = 'ranking:list'

LANGUAGE_CODE = 'pl'
TIME_ZONE = 'Europe/Warsaw'
USE_I18N = True
USE_TZ = True

# Pliki Django (panel admina) pod /static/, statyczna strona pod /
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
WHITENOISE_ROOT = PUBLIC_DIR
WHITENOISE_INDEX_FILE = True
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}

# Zdjęcia wgrywane w panelu (produkty, szkolenia). Na Northflanku katalog musi leżeć
# na trwałym wolumenie, inaczej pliki znikają przy każdym wdrożeniu.
MEDIA_URL = '/media/'
MEDIA_ROOT = Path(os.environ.get('DJANGO_MEDIA_ROOT', BASE_DIR / 'media'))

# Bramka płatności: 'dummy' = płatność testowa bez pieniędzy (patrz shop/payments.py)
PAYMENT_PROVIDER = os.environ.get('PAYMENT_PROVIDER', 'dummy')

# Poczta (SMTP, np. Gmail z hasłem aplikacji). Bez EMAIL_HOST maile wypisują się w konsoli zamiast być wysyłane.
EMAIL_HOST = os.environ.get('EMAIL_HOST', '')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
if EMAIL_HOST:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
    EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', '1') == '1'
    EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', '0') == '1'
    # Bez limitu zawieszony serwer poczty blokowałby składanie zamówień
    EMAIL_TIMEOUT = 15
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# Gmail wysyła tylko z adresu skrzynki, więc domyślnie nadawcą jest EMAIL_HOST_USER
DEFAULT_FROM_EMAIL = os.environ.get(
    'DEFAULT_FROM_EMAIL', f'Training Culture <{EMAIL_HOST_USER or "info@trainingculture.pl"}>',
)
SERVER_EMAIL = DEFAULT_FROM_EMAIL
# Na ten adres przychodzi powiadomienie o każdym opłaconym zamówieniu (puste = bez powiadomień)
SHOP_NOTIFY_EMAIL = os.environ.get('SHOP_NOTIFY_EMAIL', EMAIL_HOST_USER)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

if not DEBUG:
    # Northflank terminuje HTTPS przed kontenerem
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = os.environ.get('DJANGO_SSL_REDIRECT', '1') == '1'
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
