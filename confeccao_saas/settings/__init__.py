"""
Seletor de ambiente simples - CosturAI SaaS
"""
import os

# Detecta ambiente pela variável DJANGO_ENV
# dev = desenvolvimento local (padrão)
# prod = produção na VPS
environment = os.environ.get('DJANGO_ENV', 'dev')

if environment == 'prod':
    from .prod import *
    print("🚀 Ambiente: PRODUÇÃO")
else:
    from .dev import *
    print("🔧 Ambiente: DESENVOLVIMENTO") 