from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal


class TenantBaseModel(models.Model):
    """
    Modelo base para todos os modelos que precisam de isolamento por empresa.
    Garante que todos os dados sejam filtrados automaticamente por empresa.
    """
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Criado em")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Atualizado em")
    
    class Meta:
        abstract = True


class TenantManager(models.Manager):
    """
    Manager customizado para garantir isolamento automático por empresa.
    Será usado em todos os modelos sensíveis do sistema.
    """
    def __init__(self, *args, **kwargs):
        self.empresa_field = kwargs.pop('empresa_field', 'empresa')
        super().__init__(*args, **kwargs)
    
    def get_queryset(self):
        # TODO: Implementar filtro automático por empresa
        # Será implementado junto com o middleware
        return super().get_queryset()


class PlanoAssinatura(models.Model):
    """Planos de assinatura disponíveis no SaaS"""
    
    TIPO_CHOICES = [
        ('GRATUITO', 'Gratuito - R$ 0/mês'),
        ('BASICO', 'Básico - R$ 49/mês'),
        ('PROFISSIONAL', 'Profissional - R$ 99/mês'),
        ('ENTERPRISE', 'Enterprise - R$ 199/mês'),
    ]
    
    PERIODICIDADE_CHOICES = [
        ('MENSAL', 'Mensal'),
        ('ANUAL', 'Anual'),
        ('TRIAL', 'Trial'),
    ]
    
    nome = models.CharField(max_length=50, unique=True)
    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES)
    descricao = models.TextField(default="")
    descricao_curta = models.CharField(max_length=100, verbose_name="Descrição Curta", default="")
    
    # Preços
    preco_mensal = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    preco_anual = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    desconto_anual = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0, 
        verbose_name="Desconto Anual (%)"
    )
    
    # Limitações do plano
    max_empresas = models.IntegerField(default=1)
    max_ops_mes = models.IntegerField(default=100)
    max_usuarios = models.IntegerField(default=5)
    max_storage_gb = models.IntegerField(default=1, verbose_name="Storage (GB)")
    
    # Features
    tem_api = models.BooleanField(default=False, verbose_name="Acesso à API")
    tem_relatorios_avancados = models.BooleanField(default=False, verbose_name="Relatórios Avançados")
    tem_suporte_prioritario = models.BooleanField(default=False, verbose_name="Suporte Prioritário")
    tem_backup_automatico = models.BooleanField(default=False, verbose_name="Backup Automático")
    tem_integracao_contabil = models.BooleanField(default=False, verbose_name="Integração Contábil")
    tem_multiempresa = models.BooleanField(default=False, verbose_name="Multi-empresa")
    
    # Configurações de trial
    dias_trial = models.IntegerField(default=30, verbose_name="Dias de Trial")
    permite_trial = models.BooleanField(default=True, verbose_name="Permite Trial")
    
    # Configurações de billing
    permite_upgrade = models.BooleanField(default=True, verbose_name="Permite Upgrade")
    permite_downgrade = models.BooleanField(default=True, verbose_name="Permite Downgrade")
    requer_cartao_trial = models.BooleanField(default=False, verbose_name="Requer Cartão no Trial")
    
    # Destaque e ordenação
    destaque = models.BooleanField(default=False, verbose_name="Plano em Destaque")
    ordem_exibicao = models.IntegerField(default=0, verbose_name="Ordem de Exibição")
    cor_tema = models.CharField(max_length=7, default="#3b82f6", verbose_name="Cor do Tema (HEX)")
    
    # Status
    ativo = models.BooleanField(default=True)
    visivel_site = models.BooleanField(default=True, verbose_name="Visível no Site")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Plano de Assinatura"
        verbose_name_plural = "Planos de Assinatura"
        ordering = ['ordem_exibicao', 'preco_mensal']
    
    def __str__(self):
        return f"{self.nome} - R$ {self.preco_mensal}"
    
    @property
    def preco_anual_calculado(self):
        """Calcula o preço anual com desconto"""
        if self.preco_anual:
            return self.preco_anual
        
        preco_base_anual = self.preco_mensal * 12
        if self.desconto_anual > 0:
            desconto = preco_base_anual * (self.desconto_anual / 100)
            return preco_base_anual - desconto
        
        return preco_base_anual
    
    @property
    def economia_anual(self):
        """Calcula a economia ao pagar anualmente"""
        preco_mensal_x12 = self.preco_mensal * 12
        return preco_mensal_x12 - self.preco_anual_calculado
    
    @property
    def features_lista(self):
        """Retorna lista de features ativas"""
        features = []
        
        # Features específicas por plano para corresponder à landing page
        if self.tipo == 'GRATUITO':
            features = [
                "Até 30 dias de teste",
                "1 empresa", 
                f"{self.max_ops_mes} OPs por mês",
                "Suporte por e-mail",
                "Relatórios básicos"
            ]
        elif self.tipo == 'BASICO':
            features = [
                "1 empresa",
                f"{self.max_ops_mes} OPs por mês", 
                f"{self.max_usuarios} usuários",
                "Suporte prioritário",
                "Relatórios avançados"
            ]
        elif self.tipo == 'PROFISSIONAL':
            features = [
                f"{self.max_empresas} empresas",
                f"{self.max_ops_mes} OPs por mês",
                f"{self.max_usuarios} usuários", 
                "API incluída",
                "Relatórios premium"
            ]
        elif self.tipo == 'ENTERPRISE':
            features = [
                "Empresas ilimitadas",
                "OPs ilimitadas",
                "Usuários ilimitados",
                "Suporte 24/7",
                "Customizações",
                "Inteligência Artificial"
            ]
        else:
            # Fallback para features genéricas
            features.append(f"{self.max_ops_mes} OPs por mês")
            features.append(f"{self.max_usuarios} usuários")
            features.append(f"{self.max_empresas} empresa{'s' if self.max_empresas > 1 else ''}")
            features.append(f"{self.max_storage_gb}GB de armazenamento")
            
            # Features avançadas
            if self.tem_api:
                features.append("Acesso à API")
            if self.tem_relatorios_avancados:
                features.append("Relatórios avançados")
            if self.tem_suporte_prioritario:
                features.append("Suporte prioritário")
            if self.tem_backup_automatico:
                features.append("Backup automático")
            if self.tem_integracao_contabil:
                features.append("Integração contábil")
            if self.tem_multiempresa:
                features.append("Multi-empresa")
        
        return features
    
    def pode_fazer_upgrade_para(self, plano_destino):
        """Verifica se pode fazer upgrade para outro plano"""
        if not self.permite_upgrade:
            return False
        return plano_destino.preco_mensal > self.preco_mensal
    
    def pode_fazer_downgrade_para(self, plano_destino):
        """Verifica se pode fazer downgrade para outro plano"""
        if not self.permite_downgrade:
            return False
        return plano_destino.preco_mensal < self.preco_mensal


class Empresa(models.Model):
    """Empresas do sistema - Tenant principal"""
    
    nome = models.CharField(max_length=100, verbose_name="Nome Fantasia")
    razao_social = models.CharField(max_length=150)
    cnpj = models.CharField(max_length=18, unique=True)
    endereco = models.TextField()
    cidade = models.CharField(max_length=50)
    estado = models.CharField(max_length=2)
    cep = models.CharField(max_length=10)
    telefone = models.CharField(max_length=20)
    email = models.EmailField()
    
    # Configurações da empresa
    capacidade_produtiva = models.IntegerField(default=300, verbose_name="Capacidade Produtiva/Dia")
    logo = models.ImageField(upload_to='empresas/logos/', blank=True, null=True)
    
    # Status
    ativa = models.BooleanField(default=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
        ordering = ['nome']
    
    def __str__(self):
        return self.nome


class AssinaturaEmpresa(models.Model):
    """Controle de assinaturas das empresas"""
    
    STATUS_CHOICES = [
        ('ATIVA', 'Ativa'),
        ('SUSPENSA', 'Suspensa'),
        ('CANCELADA', 'Cancelada'),
        ('TRIAL', 'Trial'),
    ]
    
    empresa = models.OneToOneField(Empresa, on_delete=models.CASCADE, related_name='assinatura')
    plano = models.ForeignKey(PlanoAssinatura, on_delete=models.PROTECT)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='TRIAL')
    
    data_inicio = models.DateTimeField(auto_now_add=True)
    data_fim = models.DateTimeField(null=True, blank=True)
    data_proximo_pagamento = models.DateField(null=True, blank=True)
    
    # Trial
    trial_ativo = models.BooleanField(default=True)
    trial_fim = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Assinatura da Empresa"
        verbose_name_plural = "Assinaturas das Empresas"
    
    def __str__(self):
        return f"{self.empresa.nome} - {self.plano.nome} ({self.status})"


# UserProfile movido para apps.accounts.models - evitar duplicação


class UsuarioEmpresa(models.Model):
    """Relacionamento many-to-many entre usuários e empresas com roles"""
    
    ROLE_CHOICES = [
        ('ADMIN', 'Administrador'),
        ('GERENTE', 'Gerente'),
        ('OPERADOR', 'Operador'),
        ('VIEWER', 'Visualizador'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    
    ativo = models.BooleanField(default=True)
    data_vinculo = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['usuario', 'empresa']
        verbose_name = "Usuário da Empresa"
        verbose_name_plural = "Usuários das Empresas"
    
    def __str__(self):
        return f"{self.usuario.username} - {self.empresa.nome} ({self.get_role_display()})"


class AuditLog(models.Model):
    """Log de auditoria para rastrear mudanças importantes"""
    
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    
    acao = models.CharField(max_length=50)  # CREATE, UPDATE, DELETE
    modelo = models.CharField(max_length=50)  # Nome do modelo
    registro_id = models.IntegerField()
    
    dados_antes = models.JSONField(null=True, blank=True)
    dados_depois = models.JSONField(null=True, blank=True)
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Log de Auditoria"
        verbose_name_plural = "Logs de Auditoria"
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.acao} {self.modelo} #{self.registro_id} por {self.usuario}"


# ==================== MODELS DE BILLING SAAS ====================

class StatusTransacao(models.TextChoices):
    """Status das transações de pagamento"""
    PENDENTE = 'PENDENTE', 'Pendente'
    PROCESSANDO = 'PROCESSANDO', 'Processando'
    APROVADA = 'APROVADA', 'Aprovada'
    REJEITADA = 'REJEITADA', 'Rejeitada'
    CANCELADA = 'CANCELADA', 'Cancelada'
    ESTORNADA = 'ESTORNADA', 'Estornada'


class GatewayPagamento(models.TextChoices):
    """Gateways de pagamento suportados"""
    STRIPE = 'STRIPE', 'Stripe'
    MERCADOPAGO = 'MERCADOPAGO', 'Mercado Pago'
    PAGSEGURO = 'PAGSEGURO', 'PagSeguro'
    PAYPAL = 'PAYPAL', 'PayPal'
    PIX = 'PIX', 'PIX'
    BOLETO = 'BOLETO', 'Boleto'


class TipoTransacao(models.TextChoices):
    """Tipos de transação"""
    ASSINATURA = 'ASSINATURA', 'Assinatura Mensal'
    UPGRADE = 'UPGRADE', 'Upgrade de Plano'
    DOWNGRADE = 'DOWNGRADE', 'Downgrade de Plano'
    REATIVACAO = 'REATIVACAO', 'Reativação'
    CANCELAMENTO = 'CANCELAMENTO', 'Cancelamento'


class CupomDesconto(models.Model):
    """Cupons de desconto para assinaturas"""
    
    codigo = models.CharField(max_length=50, unique=True, verbose_name="Código do Cupom")
    descricao = models.CharField(max_length=200, verbose_name="Descrição")
    
    # Tipo de desconto
    tipo_desconto = models.CharField(
        max_length=20,
        choices=[
            ('PERCENTUAL', 'Percentual'),
            ('VALOR_FIXO', 'Valor Fixo'),
            ('PRIMEIRO_MES_GRATIS', 'Primeiro Mês Grátis')
        ],
        default='PERCENTUAL'
    )
    valor_desconto = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Valor/Percentual do Desconto"
    )
    
    # Limitações
    data_inicio = models.DateTimeField(verbose_name="Data de Início")
    data_fim = models.DateTimeField(verbose_name="Data de Fim")
    limite_uso = models.IntegerField(null=True, blank=True, verbose_name="Limite de Uso")
    vezes_usado = models.IntegerField(default=0, verbose_name="Vezes Usado")
    
    # Aplicabilidade
    planos_aplicaveis = models.ManyToManyField(
        PlanoAssinatura, 
        blank=True,
        verbose_name="Planos Aplicáveis"
    )
    apenas_novos_clientes = models.BooleanField(default=False)
    
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Cupom de Desconto"
        verbose_name_plural = "Cupons de Desconto"
    
    def __str__(self):
        return f"{self.codigo} - {self.valor_desconto}% OFF"
    
    @property
    def esta_valido(self):
        """Verifica se o cupom está válido"""
        from django.utils import timezone
        now = timezone.now()
        
        if not self.ativo:
            return False
        if now < self.data_inicio or now > self.data_fim:
            return False
        if self.limite_uso and self.vezes_usado >= self.limite_uso:
            return False
        
        return True
    
    def calcular_desconto(self, valor_original):
        """Calcula o valor do desconto"""
        if not self.esta_valido:
            return Decimal('0.00')
        
        if self.tipo_desconto == 'PERCENTUAL':
            return valor_original * (self.valor_desconto / 100)
        elif self.tipo_desconto == 'VALOR_FIXO':
            return min(self.valor_desconto, valor_original)
        elif self.tipo_desconto == 'PRIMEIRO_MES_GRATIS':
            return valor_original
        
        return Decimal('0.00')


class TransacaoPagamento(models.Model):
    """Transações de pagamento das assinaturas"""
    
    # Identificação
    id_transacao = models.CharField(max_length=100, unique=True, verbose_name="ID da Transação")
    id_gateway = models.CharField(max_length=200, blank=True, verbose_name="ID no Gateway")
    
    # Relacionamentos
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, verbose_name="Empresa")
    assinatura = models.ForeignKey(AssinaturaEmpresa, on_delete=models.CASCADE, related_name='transacoes')
    plano = models.ForeignKey(PlanoAssinatura, on_delete=models.PROTECT, verbose_name="Plano")
    cupom = models.ForeignKey(CupomDesconto, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Dados da transação
    tipo_transacao = models.CharField(max_length=20, choices=TipoTransacao.choices)
    gateway = models.CharField(max_length=20, choices=GatewayPagamento.choices)
    status = models.CharField(max_length=20, choices=StatusTransacao.choices, default=StatusTransacao.PENDENTE)
    
    # Valores
    valor_original = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor Original")
    valor_desconto = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Valor Desconto")
    valor_final = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor Final")
    
    # Dados do pagamento
    metodo_pagamento = models.CharField(max_length=50, blank=True, verbose_name="Método de Pagamento")
    ultimos_4_digitos = models.CharField(max_length=4, blank=True, verbose_name="Últimos 4 Dígitos")
    
    # Controle temporal
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_processamento = models.DateTimeField(null=True, blank=True)
    data_aprovacao = models.DateTimeField(null=True, blank=True)
    data_vencimento = models.DateTimeField(null=True, blank=True)
    
    # Dados adicionais
    dados_gateway = models.JSONField(default=dict, blank=True, verbose_name="Dados do Gateway")
    observacoes = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Transação de Pagamento"
        verbose_name_plural = "Transações de Pagamento"
        ordering = ['-data_criacao']
        indexes = [
            models.Index(fields=['empresa', 'status']),
            models.Index(fields=['id_gateway']),
            models.Index(fields=['data_criacao']),
        ]
    
    def __str__(self):
        return f"Transação {self.id_transacao} - {self.empresa.nome} - R$ {self.valor_final}"
    
    def save(self, *args, **kwargs):
        # Gerar ID único se não fornecido
        if not self.id_transacao:
            import uuid
            self.id_transacao = f"TXN_{uuid.uuid4().hex[:12].upper()}"
        
        # Calcular valor final
        self.valor_final = self.valor_original - self.valor_desconto
        
        super().save(*args, **kwargs)


class HistoricoAssinatura(models.Model):
    """Histórico de mudanças nas assinaturas"""
    
    assinatura = models.ForeignKey(AssinaturaEmpresa, on_delete=models.CASCADE, related_name='historico')
    plano_anterior = models.ForeignKey(
        PlanoAssinatura, 
        on_delete=models.PROTECT, 
        related_name='historico_anterior',
        null=True, blank=True
    )
    plano_novo = models.ForeignKey(
        PlanoAssinatura, 
        on_delete=models.PROTECT, 
        related_name='historico_novo'
    )
    
    acao = models.CharField(
        max_length=20,
        choices=[
            ('CRIACAO', 'Criação'),
            ('UPGRADE', 'Upgrade'),
            ('DOWNGRADE', 'Downgrade'),
            ('REATIVACAO', 'Reativação'),
            ('SUSPENSAO', 'Suspensão'),
            ('CANCELAMENTO', 'Cancelamento'),
        ]
    )
    
    valor_anterior = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    valor_novo = models.DecimalField(max_digits=10, decimal_places=2)
    valor_proporcional = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    motivo = models.TextField(blank=True, verbose_name="Motivo da Mudança")
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    data_mudanca = models.DateTimeField(auto_now_add=True)
    data_vigencia = models.DateTimeField(verbose_name="Data de Vigência")
    
    class Meta:
        verbose_name = "Histórico de Assinatura"
        verbose_name_plural = "Históricos de Assinatura"
        ordering = ['-data_mudanca']
    
    def __str__(self):
        return f"{self.acao} - {self.assinatura.empresa.nome} - {self.data_mudanca.strftime('%d/%m/%Y')}"


class ConfiguracaoBilling(models.Model):
    """Configurações globais do sistema de billing"""
    
    # Gateways
    stripe_public_key = models.CharField(max_length=200, blank=True)
    stripe_secret_key = models.CharField(max_length=200, blank=True)
    stripe_webhook_secret = models.CharField(max_length=200, blank=True)
    
    mercadopago_public_key = models.CharField(max_length=200, blank=True)
    mercadopago_access_token = models.CharField(max_length=200, blank=True)
    
    # Configurações de cobrança
    dias_trial_padrao = models.IntegerField(default=30, verbose_name="Dias de Trial Padrão")
    dias_tolerancia_pagamento = models.IntegerField(default=5, verbose_name="Dias de Tolerância")
    enviar_lembrete_pagamento = models.BooleanField(default=True)
    dias_lembrete = models.IntegerField(default=3, verbose_name="Dias Antes do Lembrete")
    
    # Impostos
    percentual_imposto = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0, 
        verbose_name="Percentual de Imposto (%)"
    )
    
    # Emails
    email_cobranca = models.EmailField(blank=True, verbose_name="Email de Cobrança")
    email_suporte = models.EmailField(blank=True, verbose_name="Email de Suporte")
    
    # Controle
    ativo = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Configuração de Billing"
        verbose_name_plural = "Configurações de Billing"
    
    def __str__(self):
        return "Configurações de Billing"
    
    @classmethod
    def get_config(cls):
        """Retorna a configuração ativa ou cria uma nova"""
        config, created = cls.objects.get_or_create(ativo=True)
        return config 