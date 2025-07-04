from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class UserProfile(models.Model):
    """Perfil estendido do usuário"""
    
    CARGO_CHOICES = [
        ('PROPRIETARIO', 'Proprietário'),
        ('GERENTE_GERAL', 'Gerente Geral'),
        ('GERENTE_PRODUCAO', 'Gerente de Produção'),
        ('GERENTE_FINANCEIRO', 'Gerente Financeiro'),
        ('SUPERVISOR', 'Supervisor'),
        ('OPERADOR', 'Operador'),
        ('VENDEDOR', 'Vendedor'),
        ('ASSISTENTE', 'Assistente'),
    ]
    
    usuario = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='profile'
    )
    
    # Informações pessoais
    cpf = models.CharField(max_length=14, blank=True, null=True, verbose_name="CPF")
    telefone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone")
    celular = models.CharField(max_length=20, blank=True, null=True, verbose_name="Celular")
    endereco = models.TextField(blank=True, null=True, verbose_name="Endereço")
    
    # Informações profissionais
    cargo = models.CharField(
        max_length=20, 
        choices=CARGO_CHOICES, 
        default='OPERADOR',
        verbose_name="Cargo"
    )
    data_admissao = models.DateField(
        auto_now_add=True, 
        verbose_name="Data de Admissão"
    )
    
    # Avatar e configurações
    avatar = models.ImageField(
        upload_to='avatars/', 
        blank=True, 
        null=True,
        verbose_name="Avatar"
    )
    
    # Configurações de notificação
    receber_email_notificacoes = models.BooleanField(
        default=True, 
        verbose_name="Receber Notificações por E-mail"
    )
    receber_sms_notificacoes = models.BooleanField(
        default=False, 
        verbose_name="Receber Notificações por SMS"
    )
    
    # Informações de acesso
    aceito_termos = models.BooleanField(
        default=False, 
        verbose_name="Aceito os Termos de Uso"
    )
    data_aceite_termos = models.DateTimeField(
        blank=True, 
        null=True,
        verbose_name="Data de Aceite dos Termos"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Perfil do Usuário"
        verbose_name_plural = "Perfis dos Usuários"
    
    def __str__(self):
        return f"Perfil de {self.usuario.get_full_name() or self.usuario.username}"
    
    @property
    def nome_completo(self):
        return self.usuario.get_full_name() or self.usuario.username
    
    @property
    def nome_cargo(self):
        return dict(self.CARGO_CHOICES).get(self.cargo, self.cargo)


class LoginHistory(models.Model):
    """Histórico de logins do usuário"""
    
    usuario = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='login_history'
    )
    
    # Informações de acesso
    ip_address = models.GenericIPAddressField(verbose_name="Endereço IP")
    user_agent = models.TextField(verbose_name="User Agent")
    
    # Localização (opcional)
    pais = models.CharField(max_length=100, blank=True, null=True, verbose_name="País")
    cidade = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cidade")
    
    # Status do login
    sucesso = models.BooleanField(default=True, verbose_name="Login com Sucesso")
    motivo_falha = models.CharField(
        max_length=200, 
        blank=True, 
        null=True,
        verbose_name="Motivo da Falha"
    )
    
    # Timestamps
    data_login = models.DateTimeField(auto_now_add=True, verbose_name="Data do Login")
    data_logout = models.DateTimeField(
        blank=True, 
        null=True, 
        verbose_name="Data do Logout"
    )
    
    class Meta:
        verbose_name = "Histórico de Login"
        verbose_name_plural = "Históricos de Login"
        ordering = ['-data_login']
    
    def __str__(self):
        status = "✓" if self.sucesso else "✗"
        return f"{status} {self.usuario.username} - {self.data_login.strftime('%d/%m/%Y %H:%M')}"
    
    @property
    def duracao_sessao(self):
        if self.data_logout:
            return self.data_logout - self.data_login
        return None


class TentativaLogin(models.Model):
    """Tentativas de login falharam para segurança"""
    
    # Pode ser por usuário ou IP
    usuario = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        blank=True, 
        null=True,
        related_name='tentativas_login'
    )
    ip_address = models.GenericIPAddressField(verbose_name="Endereço IP")
    
    # Informações da tentativa
    username_tentativa = models.CharField(
        max_length=150, 
        verbose_name="Nome de Usuário Tentado"
    )
    password_tentativa = models.CharField(
        max_length=50, 
        verbose_name="Hash da Senha (primeiros caracteres)"
    )
    
    # Timestamp
    data_tentativa = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Tentativa de Login Falhada"
        verbose_name_plural = "Tentativas de Login Falhadas"
        ordering = ['-data_tentativa']
    
    def __str__(self):
        return f"Tentativa falha: {self.username_tentativa} ({self.ip_address}) - {self.data_tentativa}"


class BloqueioIP(models.Model):
    """IPs bloqueados por tentativas de login suspeitas"""
    
    ip_address = models.GenericIPAddressField(
        unique=True, 
        verbose_name="Endereço IP"
    )
    
    # Motivo do bloqueio
    motivo = models.CharField(
        max_length=200, 
        default="Múltiplas tentativas de login falhadas",
        verbose_name="Motivo do Bloqueio"
    )
    
    # Controle de bloqueio
    bloqueado_ate = models.DateTimeField(
        verbose_name="Bloqueado Até"
    )
    tentativas_falhadas = models.IntegerField(
        default=0, 
        verbose_name="Tentativas Falhadas"
    )
    
    # Timestamps
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "IP Bloqueado"
        verbose_name_plural = "IPs Bloqueados"
        ordering = ['-criado_em']
    
    def __str__(self):
        return f"IP {self.ip_address} bloqueado até {self.bloqueado_ate}"
    
    @property
    def esta_bloqueado(self):
        return timezone.now() < self.bloqueado_ate
    
    def desbloquear(self):
        """Desbloqueia o IP"""
        self.bloqueado_ate = timezone.now()
        self.save()


class ConviteUsuario(models.Model):
    """Convites para novos usuários se juntarem a empresas"""
    
    STATUS_CHOICES = [
        ('PENDENTE', 'Pendente'),
        ('ACEITO', 'Aceito'),
        ('EXPIRADO', 'Expirado'),
        ('CANCELADO', 'Cancelado'),
    ]
    
    # Quem está convidando
    convidado_por = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='convites_enviados'
    )
    empresa = models.ForeignKey(
        'core.Empresa', 
        on_delete=models.CASCADE,
        related_name='convites'
    )
    
    # Informações do convite
    email_convidado = models.EmailField(verbose_name="E-mail do Convidado")
    nome_convidado = models.CharField(
        max_length=100, 
        verbose_name="Nome do Convidado"
    )
    cargo_sugerido = models.CharField(
        max_length=20, 
        choices=UserProfile.CARGO_CHOICES,
        default='OPERADOR',
        verbose_name="Cargo Sugerido"
    )
    role_empresa = models.CharField(
        max_length=20,
        choices=[
            ('ADMIN', 'Administrador'),
            ('GERENTE', 'Gerente'),
            ('OPERADOR', 'Operador'),
            ('VIEWER', 'Visualizador'),
        ],
        default='OPERADOR',
        verbose_name="Papel na Empresa"
    )
    
    # Controle do convite
    token = models.CharField(
        max_length=100, 
        unique=True, 
        verbose_name="Token do Convite"
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES,
        default='PENDENTE',
        verbose_name="Status"
    )
    
    # Timestamps
    criado_em = models.DateTimeField(auto_now_add=True)
    expira_em = models.DateTimeField(verbose_name="Expira Em")
    aceito_em = models.DateTimeField(
        blank=True, 
        null=True, 
        verbose_name="Aceito Em"
    )
    
    # Usuário que aceitou (se aplicável)
    usuario_aceito = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        blank=True, 
        null=True,
        related_name='convites_aceitos'
    )
    
    class Meta:
        verbose_name = "Convite de Usuário"
        verbose_name_plural = "Convites de Usuários"
        ordering = ['-criado_em']
    
    def __str__(self):
        return f"Convite para {self.email_convidado} - {self.empresa.nome}"
    
    @property
    def esta_expirado(self):
        return timezone.now() > self.expira_em
    
    def save(self, *args, **kwargs):
        if not self.expira_em:
            # Convite expira em 7 dias
            self.expira_em = timezone.now() + timedelta(days=7)
        
        if not self.token:
            import uuid
            self.token = uuid.uuid4().hex
        
        super().save(*args, **kwargs)
