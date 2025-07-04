#!/bin/bash
# =============================================================================
# CosturaAI - Script de Deploy
# =============================================================================

set -e  # Parar em caso de erro

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configurações
PROJECT_DIR="/home/deploy/costuraai"
BACKUP_DIR="/home/deploy/backups"
ENV_FILE=".env.prod"
COMPOSE_FILE="docker-compose.prod.yml"

# Função de log
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERRO:${NC} $1"
    exit 1
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] AVISO:${NC} $1"
}

# Verificar se está no diretório correto
if [ ! -f "$COMPOSE_FILE" ]; then
    error "Arquivo $COMPOSE_FILE não encontrado. Execute este script no diretório do projeto."
fi

# Verificar arquivo de ambiente
if [ ! -f "$ENV_FILE" ]; then
    error "Arquivo $ENV_FILE não encontrado. Configure o ambiente de produção primeiro."
fi

log "Iniciando deploy do CosturaAI..."

# 1. Fazer backup do banco de dados atual
log "Criando backup do banco de dados..."
./scripts/backup.sh || warning "Backup falhou, continuando deploy..."

# 2. Baixar última versão do código
log "Atualizando código..."
git pull origin main || error "Falha ao atualizar código"

# 3. Construir novas imagens
log "Construindo imagens Docker..."
docker-compose -f $COMPOSE_FILE build || error "Falha ao construir imagens"

# 4. Executar migrações
log "Executando migrações do banco de dados..."
docker-compose -f $COMPOSE_FILE run --rm web python manage.py migrate --noinput || error "Falha nas migrações"

# 5. Coletar arquivos estáticos
log "Coletando arquivos estáticos..."
docker-compose -f $COMPOSE_FILE run --rm web python manage.py collectstatic --noinput || error "Falha ao coletar estáticos"

# 6. Parar containers antigos
log "Parando containers antigos..."
docker-compose -f $COMPOSE_FILE down

# 7. Iniciar novos containers
log "Iniciando novos containers..."
docker-compose -f $COMPOSE_FILE up -d || error "Falha ao iniciar containers"

# 8. Verificar saúde dos containers
log "Verificando saúde dos containers..."
sleep 10  # Aguardar containers iniciarem

# Verificar se containers estão rodando
CONTAINERS=("costuraai_web" "costuraai_db" "costuraai_redis" "costuraai_nginx")
for container in "${CONTAINERS[@]}"; do
    if [ "$(docker ps -q -f name=$container)" ]; then
        log "✓ $container está rodando"
    else
        error "✗ $container não está rodando"
    fi
done

# 9. Verificar aplicação
log "Verificando aplicação..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/health/)
if [ "$HTTP_CODE" = "200" ]; then
    log "✓ Aplicação está respondendo (HTTP $HTTP_CODE)"
else
    error "✗ Aplicação não está respondendo (HTTP $HTTP_CODE)"
fi

# 10. Limpar imagens antigas
log "Limpando imagens Docker antigas..."
docker image prune -f

# 11. Mostrar logs recentes
log "Logs recentes da aplicação:"
docker-compose -f $COMPOSE_FILE logs --tail=20 web

log "Deploy concluído com sucesso! 🚀"
log "Acesse: https://costuraai.com.br"

# Enviar notificação (opcional)
# curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
#      -H 'Content-type: application/json' \
#      -d '{"text":"Deploy do CosturaAI concluído com sucesso! 🚀"}' 