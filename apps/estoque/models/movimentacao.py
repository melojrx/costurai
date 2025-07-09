from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.validators import MinValueValidator
from apps.core.models import TenantBaseModel


class TipoMovimentacao(models.TextChoices):
    """Tipos de movimentação de estoque expandidos"""
    
    # === ENTRADAS ===
    ENTRADA_COMPRA = 'ENTRADA_COMPRA', 'Entrada por Compra'
    ENTRADA_DEVOLUCAO = 'ENTRADA_DEVOLUCAO', 'Entrada por Devolução'
    ENTRADA_AJUSTE = 'ENTRADA_AJUSTE', 'Entrada por Ajuste'
    ENTRADA_INVENTARIO = 'ENTRADA_INVENTARIO', 'Entrada por Inventário'
    ENTRADA_PRODUCAO = 'ENTRADA_PRODUCAO', 'Entrada por Produção'
    ENTRADA_TRANSFERENCIA = 'ENTRADA_TRANSFERENCIA', 'Entrada por Transferência'
    
    # === SAÍDAS ===
    SAIDA_PRODUCAO = 'SAIDA_PRODUCAO', 'Saída para Produção'
    SAIDA_VENDA = 'SAIDA_VENDA', 'Saída para Venda'
    SAIDA_PERDA = 'SAIDA_PERDA', 'Saída por Perda/Dano'
    SAIDA_AJUSTE = 'SAIDA_AJUSTE', 'Saída por Ajuste'
    SAIDA_INVENTARIO = 'SAIDA_INVENTARIO', 'Saída por Inventário'
    SAIDA_DEVOLUCAO = 'SAIDA_DEVOLUCAO', 'Saída por Devolução'
    SAIDA_TRANSFERENCIA = 'SAIDA_TRANSFERENCIA', 'Saída por Transferência'
    SAIDA_CONSUMO = 'SAIDA_CONSUMO', 'Saída por Consumo Interno'
    
    # === TRANSFERÊNCIAS ===
    TRANSFERENCIA_ENTRADA = 'TRANSFERENCIA_ENTRADA', 'Transferência - Entrada'
    TRANSFERENCIA_SAIDA = 'TRANSFERENCIA_SAIDA', 'Transferência - Saída'
    
    @classmethod
    def get_entradas(cls):
        """Retorna todos os tipos de entrada"""
        return [
            cls.ENTRADA_COMPRA,
            cls.ENTRADA_DEVOLUCAO,
            cls.ENTRADA_AJUSTE,
            cls.ENTRADA_INVENTARIO,
            cls.ENTRADA_PRODUCAO,
            cls.ENTRADA_TRANSFERENCIA,
            cls.TRANSFERENCIA_ENTRADA,
        ]
    
    @classmethod
    def get_saidas(cls):
        """Retorna todos os tipos de saída"""
        return [
            cls.SAIDA_PRODUCAO,
            cls.SAIDA_VENDA,
            cls.SAIDA_PERDA,
            cls.SAIDA_AJUSTE,
            cls.SAIDA_INVENTARIO,
            cls.SAIDA_DEVOLUCAO,
            cls.SAIDA_TRANSFERENCIA,
            cls.SAIDA_CONSUMO,
            cls.TRANSFERENCIA_SAIDA,
        ]


class MovimentacaoEstoque(TenantBaseModel):
    """
    Registro de movimentações de estoque (Kardex).
    Cada transação é um registro imutável para auditoria completa.
    """
    empresa = models.ForeignKey(
        'core.Empresa', 
        on_delete=models.CASCADE, 
        verbose_name="Empresa"
    )
    materia_prima = models.ForeignKey(
        'estoque.MateriaPrima',
        on_delete=models.PROTECT,
        related_name='movimentacoes',
        verbose_name="Matéria-Prima"
    )

    # --- Dados da Movimentação ---
    data_movimento = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data e Hora do Movimento"
    )
    tipo_movimento = models.CharField(
        max_length=25,
        choices=TipoMovimentacao.choices,
        verbose_name="Tipo de Movimento"
    )
    quantidade = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        verbose_name="Quantidade Movimentada",
        help_text="Positivo para entradas, negativo para saídas"
    )
    custo_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Custo Unitário",
        help_text="Custo no momento da transação"
    )

    # --- Rastreabilidade ---
    numero_documento = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Número do Documento",
        help_text="Nota fiscal, pedido, etc."
    )
    lote = models.ForeignKey(
        'estoque.LoteMateriaPrima',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Lote"
    )

    # --- Relacionamento Genérico (Origem) ---
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    origem = GenericForeignKey('content_type', 'object_id')

    # --- Controle e Auditoria ---
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Usuário Responsável"
    )
    observacoes = models.TextField(
        blank=True, 
        verbose_name="Observações"
    )
    motivo_ajuste = models.TextField(
        blank=True,
        verbose_name="Motivo do Ajuste",
        help_text="Obrigatório para ajustes manuais"
    )
    
    # --- Status ---
    cancelada = models.BooleanField(
        default=False,
        verbose_name="Movimentação Cancelada"
    )
    data_cancelamento = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data do Cancelamento"
    )
    usuario_cancelamento = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='movimentacoes_canceladas',
        verbose_name="Usuário que Cancelou"
    )
    motivo_cancelamento = models.TextField(
        blank=True,
        verbose_name="Motivo do Cancelamento"
    )

    # --- Auditoria Avançada ---
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="Endereço IP"
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name="User Agent"
    )

    class Meta:
        app_label = 'estoque'
        verbose_name = "Movimentação de Estoque"
        verbose_name_plural = "Movimentações de Estoque (Kardex)"
        ordering = ['-data_movimento', '-pk']
        indexes = [
            models.Index(fields=['empresa', 'data_movimento']),
            models.Index(fields=['materia_prima', 'data_movimento']),
            models.Index(fields=['tipo_movimento']),
            models.Index(fields=['cancelada']),
        ]

    def __str__(self):
        sinal = '+' if self.quantidade >= 0 else ''
        status = ' [CANCELADA]' if self.cancelada else ''
        return (
            f"{self.materia_prima.descricao} | "
            f"{self.get_tipo_movimento_display()}: "
            f"{sinal}{self.quantidade} {self.materia_prima.unidade}"
            f"{status}"
        )

    # --- Properties ---

    @property
    def valor_total(self):
        """Calcula o valor total da movimentação"""
        return abs(self.quantidade) * self.custo_unitario

    @property
    def e_entrada(self):
        """Verifica se é uma movimentação de entrada"""
        return self.tipo_movimento in TipoMovimentacao.get_entradas()

    @property
    def e_saida(self):
        """Verifica se é uma movimentação de saída"""
        return self.tipo_movimento in TipoMovimentacao.get_saidas()

    @property
    def tipo_cor(self):
        """Retorna cor Bootstrap baseada no tipo"""
        if self.cancelada:
            return 'secondary'
        elif self.e_entrada:
            return 'success'
        elif self.e_saida:
            return 'danger'
        else:
            return 'info'

    @property
    def origem_display(self):
        """Retorna uma representação amigável da origem"""
        if self.origem:
            if hasattr(self.origem, 'numero_op'):
                return f"OP {self.origem.numero_op}"
            elif hasattr(self.origem, 'numero_nf'):
                return f"NF {self.origem.numero_nf}"
            else:
                return str(self.origem)
        return "Manual"

    # --- Métodos ---

    def cancelar(self, usuario=None, motivo=""):
        """Cancela a movimentação"""
        from django.utils import timezone
        
        if self.cancelada:
            raise ValueError("Movimentação já está cancelada")
        
        self.cancelada = True
        self.data_cancelamento = timezone.now()
        self.usuario_cancelamento = usuario
        self.motivo_cancelamento = motivo
        self.save()

        # Recalcular custo médio da matéria-prima
        from ..services import CustoMedioService
        CustoMedioService.recalcular_custo_medio_completo(self.materia_prima)

    def save(self, *args, **kwargs):
        """Override do save para validações"""
        # Validar quantidade baseada no tipo
        if self.e_entrada and self.quantidade < 0:
            self.quantidade = abs(self.quantidade)
        elif self.e_saida and self.quantidade > 0:
            self.quantidade = -abs(self.quantidade)
        
        # Validar motivo para ajustes
        if self.tipo_movimento in [TipoMovimentacao.ENTRADA_AJUSTE, TipoMovimentacao.SAIDA_AJUSTE]:
            if not self.motivo_ajuste.strip():
                raise ValueError("Motivo do ajuste é obrigatório")

        super().save(*args, **kwargs) 