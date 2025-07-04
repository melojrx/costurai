# Makefile para CosturaAI SaaS

.PHONY: help dev prod build up down logs shell migrate static test clean backup restore

# Variáveis
COMPOSE_DEV = docker-compose.yml
COMPOSE_PROD = docker-compose.prod.yml
ENV_DEV = env.dev.example
ENV_PROD = env.prod.example

# Help
help:
	@echo "Comandos disponíveis:"
	@echo "  make dev        - Iniciar ambiente de desenvolvimento"
	@echo "  make prod       - Iniciar ambiente de produção"
	@echo "  make build      - Construir imagens Docker"
	@echo "  make up         - Subir containers"
	@echo "  make down       - Parar containers"
	@echo "  make logs       - Ver logs dos containers"
	@echo "  make shell      - Abrir shell Django"
	@echo "  make migrate    - Executar migrações"
	@echo "  make static     - Coletar arquivos estáticos"
	@echo "  make test       - Executar testes"
	@echo "  make clean      - Limpar arquivos temporários"
	@echo "  make backup     - Fazer backup do banco"
	@echo "  make restore    - Restaurar backup"

# Desenvolvimento
dev:
	@echo "🔧 Iniciando ambiente de desenvolvimento..."
	@if [ ! -f .env.dev ]; then cp $(ENV_DEV) .env.dev; fi
	docker-compose -f $(COMPOSE_DEV) up

dev-build:
	@echo "🔨 Construindo imagens de desenvolvimento..."
	docker-compose -f $(COMPOSE_DEV) build

dev-down:
	@echo "🛑 Parando ambiente de desenvolvimento..."
	docker-compose -f $(COMPOSE_DEV) down

# Produção
prod:
	@echo "🚀 Iniciando ambiente de produção..."
	@if [ ! -f .env.prod ]; then echo "❌ Arquivo .env.prod não encontrado!"; exit 1; fi
	docker-compose -f $(COMPOSE_PROD) up -d

prod-build:
	@echo "🔨 Construindo imagens de produção..."
	docker-compose -f $(COMPOSE_PROD) build

prod-down:
	@echo "🛑 Parando ambiente de produção..."
	docker-compose -f $(COMPOSE_PROD) down

# Comandos gerais
logs:
	@echo "📋 Mostrando logs..."
	@if [ -f $(COMPOSE_PROD) ] && [ "$$(docker-compose -f $(COMPOSE_PROD) ps -q)" ]; then \
		docker-compose -f $(COMPOSE_PROD) logs -f; \
	else \
		docker-compose -f $(COMPOSE_DEV) logs -f; \
	fi

shell:
	@echo "🐚 Abrindo shell Django..."
	@if [ -f $(COMPOSE_PROD) ] && [ "$$(docker-compose -f $(COMPOSE_PROD) ps -q web)" ]; then \
		docker-compose -f $(COMPOSE_PROD) exec web python manage.py shell; \
	else \
		docker-compose -f $(COMPOSE_DEV) exec web python manage.py shell; \
	fi

migrate:
	@echo "🔄 Executando migrações..."
	@if [ -f $(COMPOSE_PROD) ] && [ "$$(docker-compose -f $(COMPOSE_PROD) ps -q web)" ]; then \
		docker-compose -f $(COMPOSE_PROD) exec web python manage.py migrate; \
	else \
		docker-compose -f $(COMPOSE_DEV) exec web python manage.py migrate; \
	fi

makemigrations:
	@echo "📝 Criando migrações..."
	@if [ -f $(COMPOSE_PROD) ] && [ "$$(docker-compose -f $(COMPOSE_PROD) ps -q web)" ]; then \
		docker-compose -f $(COMPOSE_PROD) exec web python manage.py makemigrations; \
	else \
		docker-compose -f $(COMPOSE_DEV) exec web python manage.py makemigrations; \
	fi

static:
	@echo "📦 Coletando arquivos estáticos..."
	@if [ -f $(COMPOSE_PROD) ] && [ "$$(docker-compose -f $(COMPOSE_PROD) ps -q web)" ]; then \
		docker-compose -f $(COMPOSE_PROD) exec web python manage.py collectstatic --noinput; \
	else \
		docker-compose -f $(COMPOSE_DEV) exec web python manage.py collectstatic --noinput; \
	fi

test:
	@echo "🧪 Executando testes..."
	@if [ -f $(COMPOSE_PROD) ] && [ "$$(docker-compose -f $(COMPOSE_PROD) ps -q web)" ]; then \
		docker-compose -f $(COMPOSE_PROD) exec web python manage.py test; \
	else \
		docker-compose -f $(COMPOSE_DEV) exec web python manage.py test; \
	fi

# Backup e Restore
backup:
	@echo "💾 Fazendo backup..."
	@if [ -x scripts/backup.sh ]; then \
		./scripts/backup.sh; \
	else \
		echo "❌ Script de backup não encontrado!"; \
	fi

restore:
	@echo "♻️  Restaurando backup..."
	@if [ -x scripts/restore.sh ]; then \
		@if [ -z "$(BACKUP_FILE)" ]; then \
			echo "❌ Especifique o arquivo: make restore BACKUP_FILE=arquivo.sql.gz"; \
		else \
			./scripts/restore.sh $(BACKUP_FILE); \
		fi \
	else \
		echo "❌ Script de restore não encontrado!"; \
	fi

# Limpeza
clean:
	@echo "🧹 Limpando arquivos temporários..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name ".DS_Store" -delete
	rm -rf staticfiles/
	rm -rf .pytest_cache/
	rm -rf .coverage
	@echo "✅ Limpeza concluída!"

# Deploy
deploy:
	@echo "🚀 Executando deploy..."
	@if [ -x scripts/deploy.sh ]; then \
		./scripts/deploy.sh; \
	else \
		echo "❌ Script de deploy não encontrado!"; \
	fi

# Comandos Docker
docker-clean:
	@echo "🐳 Limpando Docker..."
	docker system prune -f
	docker volume prune -f
	@echo "✅ Docker limpo!"

docker-stats:
	@echo "📊 Estatísticas Docker..."
	docker stats

# Desenvolvimento rápido
runserver:
	python manage.py runserver

createsuperuser:
	python manage.py createsuperuser

# Instalação local
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt 