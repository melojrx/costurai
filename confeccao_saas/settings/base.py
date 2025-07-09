"""
Configurações base do Django para CosturAI SaaS
Configurações comuns a todos os ambientes
"""

from pathlib import Path
from decouple import config # Usar decouple para gerenciar variáveis de ambiente
import os

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Application definition
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'corsheaders',
    'django_filters',
    'crispy_forms',
    'crispy_bootstrap5',
    'django_extensions',
    'debug_toolbar', # Adicionado aqui, será habilitado/desabilitado no middleware
]

LOCAL_APPS = [
    'apps.core',
    'apps.accounts',
    'apps.empresas',
    'apps.cadastros',
    'apps.producao',
    'apps.estoque',
    'apps.financeiro',
    'apps.relatorios',
    'apps.api',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    'whitenoise.middleware.WhiteNoiseMiddleware',
    "django.contrib.sessions.middleware.SessionMiddleware",
    'corsheaders.middleware.CorsMiddleware',
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    
    # Debug Toolbar (deve vir depois dos middlewares do Django)
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    
    # Nossos middlewares customizados (por último)
    'apps.core.middleware.TenantMiddleware',
    'apps.core.middleware.TenantQueryMiddleware',
]

ROOT_URLCONF = "confeccao_saas.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / 'templates'],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # Context processors customizados
                "apps.core.context_processors.empresa_context",
            ],
        },
    },
]

WSGI_APPLICATION = "confeccao_saas.wsgi.application"
ASGI_APPLICATION = "confeccao_saas.asgi.application" # Adicionado para consistência

# Database
# A configuração do banco de dados será feita em dev.py e prod.py
DATABASES = {}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 8,
        }
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
# WhiteNoise configuration
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# CORS Headers - Configuração base, será sobrescrita por ambiente
CORS_ALLOW_CREDENTIALS = True
# As origens permitidas (CORS_ALLOWED_ORIGINS) devem ser definidas em dev.py/prod.py

# Configurações de upload
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB

# Configurações de trial
TRIAL_PERIOD_DAYS = 30

# Limites por plano
PLANO_LIMITS = {
    'GRATUITO': {
        'max_empresas': 1,
        'max_ops_mes': 50,
        'max_usuarios': 2,
        'max_storage_mb': 50,
    },
    'BASICO': {
        'max_empresas': 1,
        'max_ops_mes': 200,
        'max_usuarios': 5,
        'max_storage_mb': 100,
    },
    'PROFISSIONAL': {
        'max_empresas': 3,
        'max_ops_mes': 800,
        'max_usuarios': 15,
        'max_storage_mb': 500,
    },
    'ENTERPRISE': {
        'max_empresas': -1,  # Ilimitado
        'max_ops_mes': -1,   # Ilimitado
        'max_usuarios': -1,  # Ilimitado
        'max_storage_mb': 2000,
    },
}

# URLs de autenticação
LOGIN_URL = 'accounts:login' # Usando namespace
LOGIN_REDIRECT_URL = 'dashboard' # Usando name da url
LOGOUT_REDIRECT_URL = 'home' # Usando name da url

# Logging básico
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': config('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        'apps': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Celery - Configurações base
# A URL do broker e backend será definida por ambiente
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']

# Debug Toolbar
INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
] 