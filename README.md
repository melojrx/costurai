# 🏭 CosturaAI SaaS - Sistema de Gestão para Confecções

<p align="center">
  <img src="https://img.shields.io/badge/Django-5.0.1-green.svg" alt="Django 5.0.1">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/Status-Em%20Produção-brightgreen.svg" alt="Status: Em Produção">
  <img src="https://img.shields.io/badge/Licença-Privada-red.svg" alt="Licença Privada">
</p>

## 🎯 Visão Geral

**CosturaAI** é um sistema SaaS multitenant completo para gestão empresarial de confecções, desenvolvido com Django 5. O sistema substitui planilhas Excel por uma solução web moderna, escalável e segura, baseada na análise de dados reais de empresas do setor.

### 🌟 Principais Características

- **🏢 Multitenant**: Suporte a múltiplas empresas com isolamento completo de dados
- **📊 Workflow Inteligente**: Sistema completo de acompanhamento de produção
- **💰 Gestão Financeira**: Controle de fluxo de caixa, DRE e relatórios
- **⏰ Monitoramento em Tempo Real**: Contadores de plano e avisos de vencimento
- **🎨 Interface Moderna**: Design responsivo com UX otimizada
- **🔒 Segurança Avançada**: Isolamento de dados e controle de acesso

## 🏗️ Arquitetura Multitenant

### Estratégia de Isolamento
- **Tipo**: Schema Compartilhado com Isolamento por Empresa
- **Método**: Campo `empresa_id` em todos os modelos sensíveis
- **Middleware**: Filtro automático por empresa ativa
- **Segurança**: Validação rigorosa de acesso usuário/empresa

### Estrutura de Dados
```
Empresa (Tenant)
├── Usuários (isolados por empresa)
├── Clientes e Fornecedores
├── Produtos e Materiais
├── Ordens de Produção
├── Dados Financeiros
└── Relatórios e Dashboards
```

## 📦 Estrutura do Projeto

```
confeccao_saas/
├── apps/                    # Módulos da aplicação
│   ├── core/               # Sistema base e multitenant
│   │   ├── models.py       # Modelos base (Empresa, Plano, etc.)
│   │   ├── middleware.py   # Middleware multitenant
│   │   ├── context_processors.py  # Context processors globais
│   │   └── workflow.py     # Sistema de workflow
│   ├── accounts/           # Autenticação e usuários
│   ├── empresas/          # Gestão de empresas e dashboard
│   ├── cadastros/         # Clientes, fornecedores, produtos
│   ├── producao/          # Ordens de produção e workflow
│   │   ├── models.py       # Modelos de produção
│   │   ├── views.py        # Views com workflow integrado
│   │   ├── workflow.py     # Lógica de workflow de OPs
│   │   └── urls.py         # URLs de produção
│   ├── financeiro/        # Pagamentos, fluxo de caixa
│   ├── relatorios/        # Relatórios e dashboards
│   └── api/               # API REST
├── templates/             # Templates HTML organizados
│   ├── base/              # Templates base
│   ├── auth/              # Páginas de autenticação
│   ├── empresas/          # Dashboard e gestão
│   ├── producao/          # Módulo de produção
│   └── financeiro/        # Módulo financeiro
├── static/               # CSS, JS, imagens
├── media/                # Uploads de arquivos
└── logs/                 # Logs do sistema
```

## 🚀 Tecnologias Utilizadas

### Backend
- **Django 5.0.1** - Framework web principal
- **Django REST Framework 3.14.0** - API REST
- **PostgreSQL** - Banco de dados (produção)
- **SQLite** - Banco de dados (desenvolvimento)
- **Redis 5.0.1** - Cache e sessões
- **Celery 5.3.4** - Tasks assíncronas

### Frontend
- **Bootstrap 5.3** - Framework CSS responsivo
- **FontAwesome 6** - Ícones vetoriais
- **Chart.js** - Gráficos e dashboards interativos
- **Crispy Forms** - Formulários elegantes

### Integrações de Pagamento
- **Stripe 7.10.0** - Pagamentos internacionais
- **Mercado Pago 2.2.1** - Pagamentos Brasil
- **Webhook System** - Processamento automático

### DevOps & Produção
- **WhiteNoise 6.6.0** - Servir arquivos estáticos
- **Gunicorn 21.2.0** - Servidor WSGI
- **Sentry SDK** - Monitoramento de erros
- **Django Debug Toolbar** - Debug em desenvolvimento

## 🔧 Configuração de Desenvolvimento

### 1. Pré-requisitos
```bash
# Verificar versões
python --version  # Python 3.11+
git --version     # Git 2.30+
```

### 2. Clonar e Configurar Ambiente
```bash
# Clonar repositório
git clone <repo_url>
cd confeccao_saas

# Criar ambiente virtual
python -m venv venv
source venv/Scripts/activate  # Git Bash no Windows
# ou
venv\Scripts\activate  # CMD no Windows

# Instalar dependências
pip install -r requirements.txt
```

### 3. Configurar Variáveis de Ambiente
```bash
# Copiar arquivo de exemplo
cp config.env.example config.env

# Editar configurações
# - SECRET_KEY
# - DATABASE_URL
# - STRIPE_KEYS
# - MERCADOPAGO_KEYS
```

### 4. Configurar Banco de Dados
```bash
# Aplicar migrações
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Executar setup inicial (opcional)
python setup_inicial.py
```

### 5. Executar Servidor
```bash
# Desenvolvimento
python manage.py runserver

# Produção
gunicorn confeccao_saas.wsgi:application --bind 0.0.0.0:8000
```

**Acesse**: http://127.0.0.1:8000

## 📊 Funcionalidades Implementadas

### ✅ Sistema Core (100% Concluído)
- [x] **Multitenant**: Isolamento completo por empresa
- [x] **Middleware**: Detecção automática de empresa
- [x] **Context Processors**: Dados globais em templates
- [x] **Contador de Plano**: Monitoramento de trial e vencimentos
- [x] **Sistema de Avisos**: Alertas visuais por urgência
- [x] **Auditoria**: Log completo de ações

### ✅ Módulo de Autenticação (100% Concluído)
- [x] **Cadastro Multi-step**: Empresa → Usuário → Confirmação
- [x] **Login/Logout**: Autenticação segura
- [x] **Recuperação de Senha**: Via email
- [x] **Perfis de Usuário**: Gestão de dados pessoais
- [x] **Identidade Visual**: Ícones de tesoura consistentes

### ✅ Módulo Empresas (100% Concluído)
- [x] **Dashboard Principal**: Visão geral com estatísticas
- [x] **Gestão de Empresa**: CRUD completo
- [x] **Seleção de Empresa**: Troca entre empresas
- [x] **Configurações**: Personalização por empresa

### ✅ Módulo Produção (100% Concluído)
- [x] **Workflow Completo**: 8 status de produção
- [x] **Ordens de Produção**: CRUD com validações
- [x] **Acompanhamento**: Timeline visual de progresso
- [x] **Departamentos**: Configuração de etapas
- [x] **Estatísticas**: Contadores em tempo real
- [x] **Transições**: Controle de mudanças de status

#### Sistema de Workflow de Produção
```
Cadastrada → Preparação → Frente Externa → Montagem 
    ↓
Em Produção → Concluída → Finalizada → Entregue
```

**Status Disponíveis:**
- 🟡 **Planejamento**: OP criada, aguardando início
- 🔵 **Preparação**: Separação de materiais
- 🟠 **Frente Externa**: Processos externos
- 🟣 **Montagem**: Montagem de componentes
- 🟢 **Em Produção**: Produção ativa
- ✅ **Concluída**: Produção finalizada
- 🔒 **Finalizada**: Controle de qualidade
- 🚚 **Entregue**: Entregue ao cliente

### ✅ Módulo Cadastros (90% Concluído)
- [x] **Clientes**: CRUD completo com validações
- [x] **Fornecedores**: Gestão de fornecedores
- [x] **Produtos**: Catálogo de produtos
- [x] **Materiais**: Controle de estoque
- [ ] **Integração com Produção**: Consumo automático

### ✅ Módulo Financeiro (80% Concluído)
- [x] **Contas a Pagar**: Gestão de pagamentos
- [x] **Contas a Receber**: Controle de recebimentos
- [x] **Fluxo de Caixa**: Controle diário
- [x] **Categorização**: Gastos fixos/variáveis
- [ ] **DRE Automático**: Demonstrativo de resultados
- [ ] **Relatórios Avançados**: Análises financeiras

### 🔄 Módulo API (70% Concluído)
- [x] **Endpoints Base**: CRUD para todos os modelos
- [x] **Autenticação**: Token-based auth
- [x] **Filtros**: Filtros automáticos por empresa
- [ ] **Webhooks**: Integrações externas
- [ ] **Rate Limiting**: Controle de uso

## 💰 Planos de Assinatura

| Plano | Preço Mensal | Empresas | OPs/Mês | Usuários | Recursos |
|-------|--------------|----------|---------|----------|----------|
| **Trial** | Gratuito | 1 | 50 | 3 | 30 dias grátis |
| **Básico** | R$ 49,90 | 1 | 200 | 5 | Relatórios básicos |
| **Profissional** | R$ 99,90 | 3 | 800 | 15 | + API + Relatórios avançados |
| **Enterprise** | R$ 199,90 | ∞ | ∞ | ∞ | + Suporte prioritário + Customizações |

### 🎯 Sistema de Contador de Plano
- **Monitoramento Automático**: Dias restantes do trial/mensalidade
- **Alertas Visuais**: 4 níveis de urgência (Normal, Atenção, Urgente, Crítico)
- **Cores Dinâmicas**: Verde → Azul → Amarelo → Vermelho
- **Animações**: Pulso para chamar atenção
- **Posicionamento**: Dashboard principal + indicador discreto no navbar

## 🔒 Segurança e Compliance

### Isolamento de Dados
- **Por Empresa**: Todos os dados isolados por `empresa_id`
- **Validação**: Verificação automática de acesso
- **Middleware**: Filtro transparente em todas as queries
- **Auditoria**: Log completo de todas as ações

### Autenticação e Autorização
- **Autenticação Obrigatória**: Todas as rotas protegidas
- **Roles e Permissões**: Sistema baseado em papéis
- **Sessões Seguras**: Timeout automático
- **HTTPS**: Obrigatório em produção

### Monitoramento
- **Sentry**: Monitoramento de erros em tempo real
- **Logs Estruturados**: Sistema de logs detalhado
- **Métricas**: Acompanhamento de performance
- **Alertas**: Notificações automáticas

## 📈 Baseado em Dados Reais

O sistema foi desenvolvido analisando planilhas e processos reais de empresas de confecção:

### 📊 Dados Analisados
- **3+ Empresas**: FM Gadelha, M Marciana, outras
- **20+ Ordens de Produção**: Diferentes status e complexidades
- **Transações Financeiras**: Categorizadas por tipo
- **Capacidade Produtiva**: 300+ peças/dia
- **Fluxo de Caixa**: Controle diário de entradas/saídas
- **DRE Mensal**: Receitas, custos fixos e variáveis

### 🎯 Funcionalidades Mapeadas
- ✅ **Multi-empresa**: Suporte a múltiplas empresas
- ✅ **Workflow Real**: Status baseados em processos reais
- ✅ **Capacidade**: Controle de capacidade produtiva
- ✅ **Classificação**: Gastos fixos/variáveis
- ✅ **Prazos**: Gestão de prazos e previsões
- ✅ **Relatórios**: Automação de relatórios manuais

## 🚀 Roadmap de Desenvolvimento

### ✅ Fase 1 - Core (Concluída)
- [x] Sistema multitenant
- [x] Autenticação e usuários
- [x] Dashboard principal
- [x] Contador de plano

### ✅ Fase 2 - Produção (Concluída)
- [x] Workflow completo
- [x] Ordens de produção
- [x] Acompanhamento visual
- [x] Estatísticas em tempo real

### 🔄 Fase 3 - Financeiro (Em Andamento)
- [x] Contas a pagar/receber
- [x] Fluxo de caixa
- [ ] DRE automático
- [ ] Relatórios avançados

### 📋 Fase 4 - Integrações (Planejada)
- [ ] API completa
- [ ] Webhooks
- [ ] Integrações externas
- [ ] Mobile app

### 🎯 Fase 5 - Otimizações (Planejada)
- [ ] Performance
- [ ] Escalabilidade
- [ ] Monitoramento avançado
- [ ] Backup automático

## 🛠️ Comandos Úteis

### Desenvolvimento
```bash
# Executar testes
python manage.py test

# Criar migrações
python manage.py makemigrations

# Aplicar migrações
python manage.py migrate

# Coletar arquivos estáticos
python manage.py collectstatic

# Shell Django
python manage.py shell

# Verificar sistema
python manage.py check
```

### Produção
```bash
# Deploy com Gunicorn
gunicorn confeccao_saas.wsgi:application --bind 0.0.0.0:8000 --workers 4

# Backup do banco
python manage.py dumpdata > backup.json

# Restaurar backup
python manage.py loaddata backup.json

# Limpar sessões expiradas
python manage.py clearsessions
```

## 📞 Suporte e Contato

### 🔧 Suporte Técnico
- **Email**: suporte@costuraai.com.br
- **Documentação**: Consulte a wiki do projeto
- **Issues**: Use o sistema de issues do repositório

### 📈 Suporte Comercial
- **Email**: comercial@costuraai.com.br
- **Telefone**: (11) 9999-9999
- **Site**: https://costuraai.com.br

### 🚀 Contribuição
Este é um projeto privado. Para contribuições, entre em contato com a equipe de desenvolvimento.

---

<p align="center">
  <strong>🏭 CosturaAI SaaS</strong><br>
  <em>Transformando a gestão de confecções com tecnologia</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Versão-1.0.0-brightgreen.svg" alt="Versão 1.0.0">
  <img src="https://img.shields.io/badge/Status-Produção-green.svg" alt="Status: Produção">
  <img src="https://img.shields.io/badge/Última%20Atualização-Janeiro%202025-blue.svg" alt="Última Atualização">
</p> 