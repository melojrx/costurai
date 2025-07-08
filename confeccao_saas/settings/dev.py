"""
Configurações de Desenvolvimento - CosturAI SaaS
Ambiente local com SQLite e configurações simples
"""

from .base import *
import os

# SECRET_KEY fixa para desenvolvimento
SECRET_KEY = 'dev-secret-key-costurai-2025-not-for-production'

# Debug ativado
DEBUG = True

# Hosts permitidos
ALLOWED_HOSTS = ['*']

# Database SQLite
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Cache em memória
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Email no console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'dev@costurai.com.br'

# CORS para desenvolvimento
CORS_ALLOW_ALL_ORIGINS = True

# Segurança desabilitada para dev
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Criar diretório de logs
os.makedirs(BASE_DIR / 'logs', exist_ok=True)

print("🔧 Ambiente de DESENVOLVIMENTO carregado")
print("📁 Banco de dados: SQLite (db.sqlite3)")
print("📧 Email: Console backend")
print("🔄 Cache: Memória local")
print("�� DEBUG: Ativado") 