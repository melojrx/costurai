from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from apps.core.models import TenantBaseModel
from decimal import Decimal


class StatusLote(models.TextChoices):
    """Status do lote"""
    ATIVO = 'ATIVO', 'Ativo'
    VENCIDO = 'VENCIDO', 'Vencido'
    BLOQUEADO = 'BLOQUEADO', 'Bloqueado'
    ESGOTADO = 'ESGOTADO', 'Esgotado'


class LoteMateriaPrima(TenantBaseModel):
    """
    Controla lotes específicos de matérias-primas, com validade e rastreabilidade.
    """
    empresa = models.ForeignKey(
        'core.Empresa',
        on_delete=models.CASCADE,
        verbose_name="Empresa"
    )
    materia_prima = models.ForeignKey(
        'estoque.MateriaPrima',
        on_delete=models.PROTECT,
        related_name='lotes',
        verbose_name="Matéria-Prima"
    )
    
    # --- Identificação ---
    numero_lote = models.CharField(
        max_length=50,
        verbose_name="Número do Lote",
        help_text="Número/código do lote do fornecedor"
    )
    lote_interno = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Lote Interno",
        help_text="Código interno para controle"
    )
    
    # --- Datas ---
    data_fabricacao = models.DateField(
        verbose_name="Data de Fabricação"
    )
    data_validade = models.DateField(
        null=True,
        blank=True,
        verbose_name="Data de Validade"
    )
    data_entrada = models.DateField(
        auto_now_add=True,
        verbose_name="Data de Entrada"
    )
    
    # --- Quantidades ---
    quantidade_inicial = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        validators=[MinValueValidator(0)],
        verbose_name="Quantidade Inicial",
        help_text="Quantidade recebida no lote"
    )
    
    # --- Custos ---
    custo_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        validators=[MinValueValidator(0)],
        verbose_name="Custo Unitário",
        help_text="Custo unitário na entrada"
    )
    
    # --- Fornecedor ---
    fornecedor = models.ForeignKey(
        'cadastros.Fornecedor',
        on_delete=models.PROTECT,
        verbose_name="Fornecedor"
    )
    numero_nota_fiscal = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Número da Nota Fiscal"
    )
    
    # --- Status e Controle ---
    status = models.CharField(
        max_length=10,
        choices=StatusLote.choices,
        default=StatusLote.ATIVO,
        verbose_name="Status"
    )
    bloqueado = models.BooleanField(
        default=False,
        verbose_name="Bloqueado",
        help_text="Lote bloqueado para uso"
    )
    motivo_bloqueio = models.TextField(
        blank=True,
        verbose_name="Motivo do Bloqueio"
    )
    
    # --- Localização ---
    localizacao = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Localização",
        help_text="Ex: Estante A, Prateleira 3"
    )
    
    # --- Observações ---
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações"
    )
    
    class Meta:
        app_label = 'estoque'
        verbose_name = "Lote de Matéria-Prima"
        verbose_name_plural = "Lotes de Matérias-Primas"
        ordering = ['-data_entrada', 'numero_lote']
        unique_together = ['empresa', 'materia_prima', 'numero_lote']
        indexes = [
            models.Index(fields=['numero_lote']),
            models.Index(fields=['data_validade']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.materia_prima.codigo} - Lote {self.numero_lote}"
    
    def clean(self):
        """Validações customizadas"""
        super().clean()
        
        # Validar data de validade
        if self.data_validade and self.data_fabricacao:
            if self.data_validade <= self.data_fabricacao:
                raise ValidationError(
                    "Data de validade deve ser posterior à data de fabricação"
                )
        
        # Validar se matéria-prima requer controle de lote
        if self.materia_prima and not self.materia_prima.controlar_lote:
            raise ValidationError(
                "Esta matéria-prima não está configurada para controle de lotes"
            )
    
    # --- Properties ---
    
    @property
    def quantidade_atual(self):
        """Calcula a quantidade atual do lote baseada nas movimentações"""
        from .movimentacao import MovimentacaoEstoque
        
        total = MovimentacaoEstoque.objects.filter(
            lote=self,
            cancelada=False
        ).aggregate(
            total=models.Sum('quantidade')
        )['total']
        
        return total or Decimal('0.000')
    
    @property
    def quantidade_utilizada(self):
        """Calcula quanto já foi utilizado do lote"""
        return self.quantidade_inicial - self.quantidade_atual
    
    @property
    def percentual_utilizado(self):
        """Calcula o percentual utilizado do lote"""
        if self.quantidade_inicial == 0:
            return 0
        return (self.quantidade_utilizada / self.quantidade_inicial) * 100
    
    @property
    def valor_total_atual(self):
        """Calcula o valor total atual do lote"""
        return self.quantidade_atual * self.custo_unitario
    
    @property
    def dias_para_vencimento(self):
        """Calcula quantos dias faltam para o vencimento"""
        if not self.data_validade:
            return None
        
        from django.utils import timezone
        hoje = timezone.now().date()
        delta = self.data_validade - hoje
        return delta.days
    
    @property
    def esta_vencido(self):
        """Verifica se o lote está vencido"""
        dias = self.dias_para_vencimento
        return dias is not None and dias < 0
    
    @property
    def esta_proximo_vencimento(self, dias_limite=30):
        """Verifica se está próximo do vencimento"""
        dias = self.dias_para_vencimento
        return dias is not None and 0 <= dias <= dias_limite
    
    @property
    def status_vencimento(self):
        """Status do vencimento para exibição"""
        if not self.data_validade:
            return 'sem_validade'
        elif self.esta_vencido:
            return 'vencido'
        elif self.esta_proximo_vencimento:
            return 'proximo_vencimento'
        else:
            return 'ok'
    
    @property
    def cor_vencimento(self):
        """Cor Bootstrap baseada no status de vencimento"""
        status = self.status_vencimento
        cores = {
            'sem_validade': 'secondary',
            'vencido': 'danger',
            'proximo_vencimento': 'warning',
            'ok': 'success'
        }
        return cores.get(status, 'secondary')
    
    @property
    def pode_ser_utilizado(self):
        """Verifica se o lote pode ser utilizado"""
        return (
            self.status == StatusLote.ATIVO and
            not self.bloqueado and
            not self.esta_vencido and
            self.quantidade_atual > 0
        )
    
    # --- Métodos ---
    
    def bloquear(self, motivo=""):
        """Bloqueia o lote para uso"""
        self.bloqueado = True
        self.motivo_bloqueio = motivo
        self.status = StatusLote.BLOQUEADO
        self.save()
    
    def desbloquear(self):
        """Desbloqueia o lote"""
        self.bloqueado = False
        self.motivo_bloqueio = ""
        self.status = StatusLote.ATIVO
        self.save()
    
    def atualizar_status(self):
        """Atualiza o status do lote automaticamente"""
        if self.bloqueado:
            self.status = StatusLote.BLOQUEADO
        elif self.quantidade_atual <= 0:
            self.status = StatusLote.ESGOTADO
        elif self.esta_vencido:
            self.status = StatusLote.VENCIDO
        else:
            self.status = StatusLote.ATIVO
        
        self.save(update_fields=['status'])
    
    def get_movimentacoes(self):
        """Retorna todas as movimentações deste lote"""
        from .movimentacao import MovimentacaoEstoque
        return MovimentacaoEstoque.objects.filter(
            lote=self
        ).order_by('-data_movimento')
    
    def save(self, *args, **kwargs):
        """Override do save para gerar lote interno"""
        if not self.lote_interno:
            # Gerar código interno baseado na data e sequência
            from django.utils import timezone
            hoje = timezone.now().date()
            sequencia = LoteMateriaPrima.objects.filter(
                empresa=self.empresa,
                data_entrada=hoje
            ).count() + 1
            
            self.lote_interno = f"L{hoje.strftime('%Y%m%d')}{sequencia:03d}"
        
        super().save(*args, **kwargs) 