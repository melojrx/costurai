"""
Configurações de Desenvolvimento para CosturaAI SaaS
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Database - SQLite para desenvolvimento
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Debug Toolbar
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
INTERNAL_IPS = ['127.0.0.1', 'localhost']

# Cache - Memória local para desenvolvimento
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'costuraai_cache_dev',
        'TIMEOUT': 300,
    }
}

# Sessions - Banco de dados para desenvolvimento
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Celery - Executar sincronamente em desenvolvimento
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Email - Console backend para desenvolvimento
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# CORS - Permitir localhost para desenvolvimento
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
CORS_ALLOW_CREDENTIALS = True

# WhiteNoise - Desabilitar compressão em desenvolvimento
STATICFILES_STORAGE = 'whitenoise.storage.StaticFilesStorage'

# Configurações específicas de desenvolvimento
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False

# Logging mais detalhado em desenvolvimento
LOGGING['loggers']['django']['level'] = 'DEBUG'
LOGGING['loggers']['apps']['level'] = 'DEBUG'

# Stripe Test Keys (desenvolvimento)
STRIPE_PUBLIC_KEY = config('STRIPE_PUBLIC_KEY_TEST', default='')
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY_TEST', default='')
STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET_TEST', default='')

# Mercado Pago Test Keys (desenvolvimento)
MERCADOPAGO_PUBLIC_KEY = config('MERCADOPAGO_PUBLIC_KEY_TEST', default='')
MERCADOPAGO_ACCESS_TOKEN = config('MERCADOPAGO_ACCESS_TOKEN_TEST', default='')

print("🔧 Ambiente de DESENVOLVIMENTO carregado") 