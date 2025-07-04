# Importar configurações baseadas na variável de ambiente
import os

environment = os.environ.get('DJANGO_ENV', 'dev')

if environment == 'prod':
    from .prod import *
elif environment == 'staging':
    from .staging import *
else:
    from .dev import * 