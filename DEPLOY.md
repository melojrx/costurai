# 🚀 Guia de Deploy - CosturAI SaaS

Este guia detalha o processo completo de deploy do CosturAI em uma VPS Ubuntu 22.04.

## 📋 Pré-requisitos

### VPS Requirements
- **OS**: Ubuntu 22.04 LTS
- **RAM**: Mínimo 2GB (recomendado 4GB)
- **CPU**: 2 vCPUs
- **Disco**: 40GB SSD
- **IP**: 145.223.92.74
- **Domínio**: costuraai.com.br

### Ferramentas Locais
- Git
- SSH client
- Editor de texto

## 🏗️ Arquitetura de Deploy

```
┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │
│   Cloudflare    │────▶│     Nginx       │
│   DNS + CDN     │     │   (Reverse      │
│                 │     │    Proxy)       │
└─────────────────┘     └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │                 │
                        │   Django App    │
                        │   (Gunicorn)    │
                        │                 │
                        └────┬────────┬───┘
                             │        │
                    ┌────────▼───┐ ┌──▼──────┐
                    │            │ │         │
                    │ PostgreSQL │ │  Redis  │
                    │            │ │         │
                    └────────────┘ └─────────┘
```

## 🔧 Configuração Inicial da VPS

### 1. Acesso inicial à VPS

```bash
# Conectar via SSH
ssh root@145.223.92.74

# Executar script de setup inicial
wget https://raw.githubusercontent.com/seu-repo/costuraai/main/scripts/setup-vps.sh
chmod +x setup-vps.sh
./setup-vps.sh
```

### 2. Configurar usuário deploy

```bash
# Adicionar chave SSH para usuário deploy
su - deploy
mkdir ~/.ssh
echo "sua-chave-publica-ssh" >> ~/.ssh/authorized_keys
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
exit
```

### 3. Clonar repositório

```bash
# Como usuário deploy
su - deploy
cd ~
git clone https://github.com/seu-usuario/costuraai.git
cd costuraai
```

## 🔐 Configuração de Ambiente

### 1. Criar arquivo de produção

```bash
# Copiar template
cp env.prod.example .env.prod

# Editar com valores reais
vim .env.prod
```

### 2. Configurações importantes

```env
# Gerar SECRET_KEY segura
SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')

# Configurar banco de dados
DB_NAME=costuraai_prod
DB_USER=costuraai_user
DB_PASSWORD=senha-muito-forte-aqui

# Redis
REDIS_PASSWORD=outra-senha-forte

# Email (exemplo com Gmail)
EMAIL_HOST_USER=seu-email@gmail.com
EMAIL_HOST_PASSWORD=senha-de-app-gmail

# Domínio
ALLOWED_HOSTS=costuraai.com.br,www.costuraai.com.br,145.223.92.74
```

## 🐳 Deploy com Docker

### 1. Build inicial

```bash
# Construir imagens
docker-compose -f docker-compose.prod.yml build

# Verificar imagens
docker images | grep costuraai
```

### 2. Iniciar serviços base

```bash
# Iniciar apenas banco e Redis primeiro
docker-compose -f docker-compose.prod.yml up -d db redis

# Verificar logs
docker-compose -f docker-compose.prod.yml logs db
docker-compose -f docker-compose.prod.yml logs redis
```

### 3. Executar migrações

```bash
# Criar banco e executar migrações
docker-compose -f docker-compose.prod.yml run --rm web python manage.py migrate

# Criar superusuário
docker-compose -f docker-compose.prod.yml run --rm web python manage.py createsuperuser
```

### 4. Coletar arquivos estáticos

```bash
docker-compose -f docker-compose.prod.yml run --rm web python manage.py collectstatic --noinput
```

### 5. Iniciar aplicação completa

```bash
# Usar script de deploy
chmod +x scripts/*.sh
./scripts/deploy.sh

# Ou manualmente
docker-compose -f docker-compose.prod.yml up -d
```

## 🔒 Configuração SSL

### 1. Instalar certificado Let's Encrypt

```bash
# Como root
certbot --nginx -d costuraai.com.br -d www.costuraai.com.br --email ssl@costuraai.com.br --agree-tos
```

### 2. Auto-renovação

```bash
# Testar renovação
certbot renew --dry-run

# Cron para renovação automática (já configurado)
# 0 0 * * 0 certbot renew --quiet
```

## 📊 Monitoramento

### 1. Verificar status dos containers

```bash
# Status geral
docker ps

# Logs em tempo real
docker-compose -f docker-compose.prod.yml logs -f

# Logs específicos
docker logs costuraai_web --tail 100
docker logs costuraai_celery --tail 100
```

### 2. Monitorar recursos

```bash
# Script de monitoramento
./monitor.sh

# Uso de recursos por container
docker stats

# Espaço em disco
df -h
du -sh /var/lib/docker/
```

### 3. Verificar aplicação

```bash
# Health check interno
curl http://localhost/health/

# Verificar HTTPS
curl -I https://costuraai.com.br

# Testar API
curl https://costuraai.com.br/api/health/
```

## 🔄 Atualizações

### 1. Deploy de nova versão

```bash
# Atualizar código
cd /home/deploy/costuraai
git pull origin main

# Executar deploy
./scripts/deploy.sh
```

### 2. Rollback

```bash
# Voltar para versão anterior
git checkout <commit-anterior>

# Re-deploy
./scripts/deploy.sh
```

## 💾 Backup e Restauração

### 1. Backup manual

```bash
./scripts/backup.sh
```

### 2. Backup automático

```bash
# Verificar cron
crontab -l

# Logs de backup
tail -f /home/deploy/logs/backup.log
```

### 3. Restaurar backup

```bash
# Listar backups disponíveis
ls -la /backups/

# Restaurar
./scripts/restore.sh /backups/costuraai_backup_20240115_030000.sql.gz
```

## 🚨 Troubleshooting

### Problemas comuns

#### 1. Container não inicia
```bash
# Verificar logs
docker logs costuraai_web

# Verificar configurações
docker-compose -f docker-compose.prod.yml config
```

#### 2. Erro 502 Bad Gateway
```bash
# Verificar se Django está rodando
docker exec costuraai_web curl http://localhost:8000/health/

# Reiniciar Nginx
docker restart costuraai_nginx
```

#### 3. Banco de dados não conecta
```bash
# Testar conexão
docker exec costuraai_web python manage.py dbshell

# Verificar variáveis
docker exec costuraai_web env | grep DB_
```

#### 4. Arquivos estáticos não carregam
```bash
# Re-coletar estáticos
docker-compose -f docker-compose.prod.yml run --rm web python manage.py collectstatic --noinput --clear

# Verificar permissões
ls -la staticfiles/
```

## 📈 Otimizações de Performance

### 1. Configurar cache no Nginx

```nginx
# Em nginx/conf.d/costuraai.conf
location /static/ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### 2. Otimizar PostgreSQL

```sql
-- Conectar ao banco
docker exec -it costuraai_db psql -U costuraai_user -d costuraai_prod

-- Analisar queries lentas
SELECT query, calls, mean_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
```

### 3. Monitorar Redis

```bash
# Conectar ao Redis
docker exec -it costuraai_redis redis-cli -a $REDIS_PASSWORD

# Verificar uso de memória
INFO memory

# Verificar keys
DBSIZE
```

## 🔐 Segurança

### 1. Firewall

```bash
# Verificar regras
ufw status verbose

# Permitir apenas necessário
ufw allow from <seu-ip> to any port 22
```

### 2. Fail2ban

```bash
# Status
fail2ban-client status

# Ver IPs bloqueados
fail2ban-client status sshd
```

### 3. Atualizações de segurança

```bash
# Atualizações automáticas
apt install unattended-upgrades
dpkg-reconfigure -plow unattended-upgrades
```

## 📞 Suporte e Manutenção

### Logs importantes

- **Aplicação**: `/home/deploy/logs/django.log`
- **Nginx**: `/home/deploy/logs/nginx/`
- **Backup**: `/home/deploy/logs/backup.log`
- **Docker**: `journalctl -u docker`

### Comandos úteis

```bash
# Reiniciar tudo
docker-compose -f docker-compose.prod.yml restart

# Parar tudo
docker-compose -f docker-compose.prod.yml down

# Limpar sistema
docker system prune -a

# Backup de emergência
docker exec costuraai_db pg_dump -U $DB_USER $DB_NAME | gzip > backup_emergencia.sql.gz
```

### Contatos de emergência

- **DevOps**: devops@costuraai.com.br
- **Suporte**: suporte@costuraai.com.br
- **Telefone**: (11) 9999-9999

---

## 🎯 Checklist de Deploy

- [ ] VPS configurada com Ubuntu 22.04
- [ ] Usuário deploy criado
- [ ] Docker e Docker Compose instalados
- [ ] Repositório clonado
- [ ] Arquivo .env.prod configurado
- [ ] Containers construídos
- [ ] Banco de dados migrado
- [ ] Arquivos estáticos coletados
- [ ] Aplicação rodando
- [ ] SSL configurado
- [ ] DNS apontando para VPS
- [ ] Backup automático configurado
- [ ] Monitoramento ativo
- [ ] Documentação atualizada

---

**Última atualização**: Janeiro 2025  
**Versão**: 1.0.0 