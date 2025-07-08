#!/bin/bash
# =============================================================================
# CosturAI - Script de Restauração de Backup
# =============================================================================

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

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

# Verificar parâmetros
if [ $# -eq 0 ]; then
    echo "Uso: $0 <arquivo_backup.sql.gz>"
    echo "Exemplo: $0 /backups/costurai_backup_20240115_120000.sql.gz"
    exit 1
fi

BACKUP_FILE=$1
DB_CONTAINER="costurai_db"

# Verificar se arquivo existe
if [ ! -f "$BACKUP_FILE" ]; then
    error "Arquivo de backup não encontrado: $BACKUP_FILE"
fi

warning "ATENÇÃO: Este processo irá SUBSTITUIR todos os dados atuais do banco!"
read -p "Tem certeza que deseja continuar? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    log "Restauração cancelada."
    exit 0
fi

log "Iniciando restauração do backup: $BACKUP_FILE"

# Parar aplicação
log "Parando aplicação..."
docker-compose -f docker-compose.prod.yml stop web celery celery-beat

# Criar backup de segurança atual
log "Criando backup de segurança do banco atual..."
./scripts/backup.sh

# Descomprimir arquivo se necessário
if [[ $BACKUP_FILE == *.gz ]]; then
    log "Descomprimindo arquivo..."
    gunzip -c $BACKUP_FILE > /tmp/restore.sql
    RESTORE_FILE="/tmp/restore.sql"
else
    RESTORE_FILE=$BACKUP_FILE
fi

# Restaurar banco
log "Restaurando banco de dados..."
docker exec -i $DB_CONTAINER psql -U $DB_USER -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"
docker exec -i $DB_CONTAINER psql -U $DB_USER -d postgres -c "CREATE DATABASE $DB_NAME;"
docker exec -i $DB_CONTAINER psql -U $DB_USER -d $DB_NAME < $RESTORE_FILE

# Limpar arquivo temporário
if [ -f "/tmp/restore.sql" ]; then
    rm /tmp/restore.sql
fi

# Executar migrações
log "Executando migrações..."
docker-compose -f docker-compose.prod.yml run --rm web python manage.py migrate --noinput

# Reiniciar aplicação
log "Reiniciando aplicação..."
docker-compose -f docker-compose.prod.yml up -d

# Aguardar aplicação iniciar
sleep 10

# Verificar saúde
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/health/)
if [ "$HTTP_CODE" = "200" ]; then
    log "✓ Aplicação restaurada e funcionando!"
else
    error "✗ Aplicação não está respondendo após restauração"
fi

log "Restauração concluída com sucesso!" 