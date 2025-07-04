#!/bin/bash
# =============================================================================
# CosturaAI - Script de Configuração Inicial da VPS
# =============================================================================
# Execute este script como root na VPS Ubuntu 22.04

set -e

# Cores
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

# Verificar se é root
if [ "$EUID" -ne 0 ]; then 
    error "Execute este script como root"
fi

log "Iniciando configuração da VPS para CosturaAI..."

# 1. Atualizar sistema
log "Atualizando sistema..."
apt update && apt upgrade -y

# 2. Instalar dependências básicas
log "Instalando dependências..."
apt install -y \
    curl \
    wget \
    git \
    vim \
    htop \
    ufw \
    fail2ban \
    nginx \
    certbot \
    python3-certbot-nginx \
    postgresql-client \
    redis-tools

# 3. Instalar Docker
log "Instalando Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

# 4. Instalar Docker Compose
log "Instalando Docker Compose..."
curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# 5. Criar usuário deploy
log "Criando usuário deploy..."
useradd -m -s /bin/bash deploy
usermod -aG docker deploy

# 6. Configurar firewall
log "Configurando firewall..."
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# 7. Configurar fail2ban
log "Configurando fail2ban..."
cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
systemctl enable fail2ban
systemctl start fail2ban

# 8. Configurar swap
log "Configurando swap..."
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab

# 9. Otimizações do sistema
log "Aplicando otimizações do sistema..."
cat >> /etc/sysctl.conf << EOF

# Otimizações CosturaAI
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.ip_local_port_range = 1024 65535
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 30
net.core.netdev_max_backlog = 65535
vm.swappiness = 10
EOF

sysctl -p

# 10. Criar estrutura de diretórios
log "Criando estrutura de diretórios..."
mkdir -p /home/deploy/{costuraai,backups,logs}
chown -R deploy:deploy /home/deploy

# 11. Configurar logrotate
log "Configurando rotação de logs..."
cat > /etc/logrotate.d/costuraai << EOF
/home/deploy/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 deploy deploy
    sharedscripts
    postrotate
        docker exec costuraai_web kill -USR1 1
    endscript
}
EOF

# 12. Criar script de monitoramento
log "Criando script de monitoramento..."
cat > /home/deploy/monitor.sh << 'EOF'
#!/bin/bash
# Monitoramento básico

echo "=== Status do Sistema ==="
echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}')%"
echo "Memória: $(free -m | awk 'NR==2{printf "%.2f%%", $3*100/$2}')"
echo "Disco: $(df -h / | awk 'NR==2{print $5}')"
echo ""
echo "=== Containers Docker ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "=== Últimos logs ==="
docker logs --tail 10 costuraai_web 2>&1 | grep ERROR || echo "Sem erros recentes"
EOF

chmod +x /home/deploy/monitor.sh
chown deploy:deploy /home/deploy/monitor.sh

# 13. Configurar backup automático via cron
log "Configurando backup automático..."
cat > /etc/cron.d/costuraai-backup << EOF
# Backup diário às 3 AM
0 3 * * * deploy cd /home/deploy/costuraai && ./scripts/backup.sh >> /home/deploy/logs/backup.log 2>&1
EOF

# 14. Instalar certificado SSL
log "Configurando SSL..."
echo "Para configurar SSL, execute após o deploy:"
echo "certbot --nginx -d costuraai.com.br -d www.costuraai.com.br"

# 15. Mensagem final
log "Configuração inicial concluída!"
echo ""
echo "Próximos passos:"
echo "1. Clone o repositório em /home/deploy/costuraai"
echo "2. Configure o arquivo .env.prod"
echo "3. Execute o script de deploy"
echo "4. Configure o certificado SSL com Certbot"
echo ""
echo "Comandos úteis:"
echo "- su - deploy (mudar para usuário deploy)"
echo "- cd /home/deploy/costuraai"
echo "- ./scripts/deploy.sh"
echo "- docker-compose -f docker-compose.prod.yml logs -f"
echo ""
log "VPS pronta para deploy! 🚀" 