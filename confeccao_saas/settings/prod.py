"""
Configurações de Produção para CosturaAI SaaS
"""

from .base import *
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

# Segurança
DEBUG = False

# Hosts permitidos - adicionar domínio real
ALLOWED_HOSTS = [
    'costuraai.com.br',
    'www.costuraai.com.br',
    '145.223.92.74',
    'localhost',  # Para healthchecks internos
]

# Database - PostgreSQL para produção
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='db'),
        'PORT': config('DB_PORT', default='5432'),
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'connect_timeout': 10,
        }
    }
}

# Cache - Redis para produção
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://redis:6379/1'),
        'KEY_PREFIX': 'costuraai',
        'TIMEOUT': 300,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'PARSER_CLASS': 'redis.connection.HiredisParser',
        }
    }
}

# Sessions - Redis para produção
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 86400  # 24 horas
SESSION_SAVE_EVERY_REQUEST = False

# Celery - Configuração para produção
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://redis:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://redis:6379/0')
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_TIME_LIMIT = 300  # 5 minutos
CELERY_TASK_SOFT_TIME_LIMIT = 240  # 4 minutos

# Email - SMTP para produção
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
SERVER_EMAIL = config('SERVER_EMAIL', default='servidor@costuraai.com.br')

# CORS - Domínios permitidos em produção
CORS_ALLOWED_ORIGINS = [
    "https://costuraai.com.br",
    "https://www.costuraai.com.br",
    "https://app.costuraai.com.br",
]
CORS_ALLOW_CREDENTIALS = True

# Segurança HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000  # 1 ano
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = 'DENY'

# Cookies
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# WhiteNoise - Compressão de arquivos estáticos
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
WHITENOISE_COMPRESS_OFFLINE = True
WHITENOISE_COMPRESSION_QUALITY = 80

# Sentry - Monitoramento de erros
if config('SENTRY_DSN', default=''):
    sentry_sdk.init(
        dsn=config('SENTRY_DSN'),
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=False,
        environment="production",
        release=config('RELEASE_VERSION', default='1.0.0'),
    )

# Stripe Production Keys
STRIPE_PUBLIC_KEY = config('STRIPE_PUBLIC_KEY_LIVE')
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY_LIVE')
STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET_LIVE')

# Mercado Pago Production Keys
MERCADOPAGO_PUBLIC_KEY = config('MERCADOPAGO_PUBLIC_KEY_LIVE')
MERCADOPAGO_ACCESS_TOKEN = config('MERCADOPAGO_ACCESS_TOKEN_LIVE')

# Configurações de performance
CONN_MAX_AGE = 600  # Reutilizar conexões de banco
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB

# Backup automático
DBBACKUP_STORAGE = 'django.core.files.storage.FileSystemStorage'
DBBACKUP_STORAGE_OPTIONS = {'location': '/backups/'}

print("🚀 Ambiente de PRODUÇÃO carregado") 