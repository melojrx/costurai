# 🚀 CosturAI - Configuração Simples

## 📋 Visão Geral

Configuração simplificada com apenas 2 ambientes:
- **DEV**: Desenvolvimento local (SQLite + Python)
- **PROD**: Produção VPS (Docker + PostgreSQL + Nginx)

## 🔧 Desenvolvimento Local

### Pré-requisitos
- Python 3.8+
- Git

### Setup Rápido
```bash
# 1. Clonar repositório
git clone <repo>
cd costurai

# 2. Criar ambiente virtual
python -m venv venv

# 3. Ativar ambiente (Windows)
venv\Scripts\activate

# 4. Instalar dependências
pip install -r requirements.txt

# 5. Executar migrações
python manage.py migrate

# 6. Criar superusuário
python manage.py createsuperuser

# 7. Rodar servidor
python manage.py runserver
```

### ✅ Funcionalidades DEV
- SQLite automático (db.sqlite3)
- Debug ativado
- Email no console
- Cache em memória
- Sem arquivos .env necessários
- SECRET_KEY hardcoded (seguro para dev)

## 🚀 Produção (VPS)

### Pré-requisitos VPS
- Ubuntu 22.04
- Docker + Docker Compose
- Domínio apontando para VPS

### Setup Produção
```bash
# 1. Clonar na VPS
git clone <repo> /home/deploy/costurai
cd /home/deploy/costurai

# 2. Criar arquivo .env.prod
cp env.prod.example .env.prod
vim .env.prod  # Configurar valores reais

# 3. Executar deploy
export DJANGO_ENV=prod
./scripts/deploy.sh
```

### ✅ Funcionalidades PROD
- PostgreSQL
- Redis para cache
- Nginx proxy reverso
- SSL automático
- Email SMTP
- Logs em arquivo

## 📁 Estrutura Simplificada

```
costurai/
├── confeccao_saas/settings/
│   ├── __init__.py      # Seletor automático
│   ├── base.py          # Configurações comuns
│   ├── dev.py           # DEV (versionado)
│   └── prod.py          # PROD (versionado)
├── .env.prod            # Produção (NÃO versionado)
├── env.prod.example     # Template
└── db.sqlite3           # Banco dev (NÃO versionado)
```

## 🔄 Como Funciona

### Seleção Automática
- **Sem DJANGO_ENV**: Usa DEV automaticamente
- **DJANGO_ENV=prod**: Usa PROD

### Desenvolvimento
```bash
# Sempre usa DEV (padrão)
python manage.py runserver
```

### Produção
```bash
# Define ambiente e usa PROD
export DJANGO_ENV=prod
docker-compose up
```

## 📝 Arquivo .env.prod

```env
# Obrigatório
DJANGO_ENV=prod
SECRET_KEY=sua-chave-secreta-forte

# Banco
DB_NAME=costurai_prod
DB_USER=costurai_user
DB_PASSWORD=senha-forte-banco

# Email
EMAIL_HOST_USER=noreply@costurai.com.br
EMAIL_HOST_PASSWORD=senha-email
```

## 🛠️ Comandos Úteis

### Desenvolvimento
```bash
python manage.py runserver      # Iniciar servidor
python manage.py migrate        # Migrações
python manage.py createsuperuser # Admin
python manage.py shell          # Shell Django
```

### Produção
```bash
./scripts/deploy.sh             # Deploy completo
docker-compose logs -f          # Ver logs
./scripts/backup.sh             # Backup
```

## 🔐 Segurança

- **DEV**: SECRET_KEY hardcoded, sem SSL
- **PROD**: SECRET_KEY do .env, SSL obrigatório
- **Arquivos sensíveis**: Não versionados (.gitignore)

## 🚨 Troubleshooting

### Erro de módulo não encontrado
```bash
# Verificar se ambiente virtual está ativo
source venv/Scripts/activate  # Windows
```

### Erro de migração
```bash
python manage.py makemigrations
python manage.py migrate
```

### Servidor não inicia (DEV)
```bash
# Verificar configuração
python manage.py check
```

### Container não inicia (PROD)
```bash
# Ver logs
docker-compose logs
```

## 📞 Suporte

- **DEV**: Logs no console
- **PROD**: Logs em `/home/deploy/logs/django.log`

---

**Configuração**: Simples e funcional ✅  
**Última atualização**: Janeiro 2025 