# Build stage
FROM python:3.11-slim as builder

# Instalar dependências do sistema necessárias para compilação
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Criar diretório de trabalho
WORKDIR /app

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Production stage
FROM python:3.11-slim

# Variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=confeccao_saas.settings

# Instalar dependências do sistema para runtime
RUN apt-get update && apt-get install -y \
    libpq-dev \
    netcat-traditional \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Criar usuário não-root
RUN groupadd -r django && useradd -r -g django django

# Criar diretórios necessários
RUN mkdir -p /app /app/staticfiles /app/media /app/logs && \
    chown -R django:django /app

WORKDIR /app

# Copiar wheels do builder e instalar
COPY --from=builder /app/wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt && \
    rm -rf /wheels

# Copiar código da aplicação
COPY --chown=django:django . .

# Criar script de entrada
RUN echo '#!/bin/sh\n\
set -e\n\
\n\
# Esperar pelo banco de dados\n\
if [ "$DATABASE_URL" ]; then\n\
    echo "Aguardando banco de dados..."\n\
    while ! nc -z $DB_HOST ${DB_PORT:-5432}; do\n\
        sleep 0.1\n\
    done\n\
    echo "Banco de dados disponível"\n\
fi\n\
\n\
# Executar migrações se habilitado\n\
if [ "$RUN_MIGRATIONS" = "true" ]; then\n\
    echo "Executando migrações..."\n\
    python manage.py migrate --noinput\n\
fi\n\
\n\
# Coletar arquivos estáticos se habilitado\n\
if [ "$COLLECT_STATIC" = "true" ]; then\n\
    echo "Coletando arquivos estáticos..."\n\
    python manage.py collectstatic --noinput\n\
fi\n\
\n\
# Criar superusuário se variáveis estiverem definidas\n\
if [ "$DJANGO_SUPERUSER_USERNAME" ] && [ "$DJANGO_SUPERUSER_EMAIL" ] && [ "$DJANGO_SUPERUSER_PASSWORD" ]; then\n\
    echo "Criando superusuário..."\n\
    python manage.py createsuperuser --noinput || true\n\
fi\n\
\n\
exec "$@"' > /app/docker-entrypoint.sh && \
    chmod +x /app/docker-entrypoint.sh

# Mudar para usuário não-root
USER django

# Expor porta
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Entrypoint e comando padrão
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "confeccao_saas.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--threads", "2", "--worker-class", "sync", "--worker-tmp-dir", "/dev/shm", "--access-logfile", "-", "--error-logfile", "-"] 