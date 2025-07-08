#!/bin/bash
# =============================================================================
# CosturAI - Script de Backup
# =============================================================================

set -e

# Configurações
BACKUP_DIR="/backups"
DB_CONTAINER="costurai_db"
RETENTION_DAYS=30
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="costurai_backup_${DATE}.sql"

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERRO:${NC} $1"
    exit 1
}

# Criar diretório de backup se não existir
mkdir -p $BACKUP_DIR

log "Iniciando backup do banco de dados..."

# Fazer backup do PostgreSQL
docker exec $DB_CONTAINER pg_dump -U $DB_USER -d $DB_NAME > $BACKUP_DIR/$BACKUP_FILE || error "Falha ao criar backup"

# Comprimir backup
log "Comprimindo backup..."
gzip $BACKUP_DIR/$BACKUP_FILE

log "Backup criado: ${BACKUP_FILE}.gz"

# Fazer backup dos arquivos de media (opcional)
if [ -d "/app/media" ]; then
    log "Fazendo backup dos arquivos de media..."
    tar -czf $BACKUP_DIR/media_${DATE}.tar.gz -C /app media/
fi

# Limpar backups antigos
log "Removendo backups com mais de $RETENTION_DAYS dias..."
find $BACKUP_DIR -name "costurai_backup_*.gz" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "media_*.tar.gz" -mtime +$RETENTION_DAYS -delete

# Listar backups atuais
log "Backups disponíveis:"
ls -lh $BACKUP_DIR/*.gz | tail -5

# Verificar espaço em disco
DISK_USAGE=$(df -h $BACKUP_DIR | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    log "AVISO: Uso de disco em $DISK_USAGE%"
fi

log "Backup concluído com sucesso!"

# Upload para S3 (opcional)
# aws s3 cp $BACKUP_DIR/${BACKUP_FILE}.gz s3://seu-bucket/backups/ 