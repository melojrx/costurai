"""
Arquivo seletor de ambiente.

Este arquivo carrega as configurações corretas (dev ou prod)
baseado na variável de ambiente DJANGO_ENV.

Para desenvolvimento local, rode com:
DJANGO_ENV=dev python manage.py runserver

Para produção, o servidor de aplicação (Gunicorn) deve setar:
DJANGO_ENV=prod
"""

import os
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()

# Obtém o ambiente, padrão para 'dev' se não especificado
ENVIRONMENT = os.getenv('DJANGO_ENV', 'dev')

print(f"=========================================")
print(f"Iniciando aplicação no ambiente: {ENVIRONMENT.upper()}")
print(f"=========================================")

if ENVIRONMENT == 'prod':
    from .settings.prod import *
else:
    from .settings.dev import *
