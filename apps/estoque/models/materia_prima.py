from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from apps.core.models import TenantBaseModel
from .movimentacao import TipoMovimentacao


class CategoriaMateriaPrima(TenantBaseModel):
    """Categorias para organizar matérias-primas"""
    empresa = models.ForeignKey(
        'core.Empresa', 
        on_delete=models.CASCADE, 
        verbose_name="Empresa"
    )
    nome = models.CharField(max_length=100, verbose_name="Nome da Categoria")
    descricao = models.TextField(blank=True, verbose_name="Descrição")
    cor_hex = models.CharField(
        max_length=7, 
        default='#3b82f6', 
        verbose_name="Cor",
        help_text="Cor hexadecimal para identificação visual"
    )
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    
    class Meta:
        app_label = 'estoque'
        verbose_name = "Categoria de Matéria-Prima"
        verbose_name_plural = "Categorias de Matérias-Primas"
        ordering = ['nome']
        unique_together = ['empresa', 'nome']
    
    def __str__(self):
        return self.nome


class MateriaPrima(TenantBaseModel):
    """
    Catálogo de matérias-primas com controle de estoque dinâmico.
    O estoque é calculado em tempo real baseado nas movimentações.
    """
    empresa = models.ForeignKey(
        'core.Empresa', 
        on_delete=models.CASCADE, 
        verbose_name="Empresa"
    )

    # --- Identificação ---
    codigo = models.CharField(
        max_length=20,
        verbose_name="Código",
        help_text="Código interno da matéria-prima"
    )
    codigo_barras = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Código de Barras",
        help_text="Código de barras ou QR Code (opcional)"
    )
    descricao = models.CharField(
        max_length=255, 
        verbose_name="Descrição da Matéria-Prima"
    )

    # --- Classificação ---
    categoria = models.ForeignKey(
        CategoriaMateriaPrima,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Categoria"
    )

    # --- Unidade de Medida ---
    UNIDADE_CHOICES = [
        ('UN', 'Unidade'),
        ('PC', 'Peça'),
        ('MT', 'Metro'),
        ('M2', 'Metro Quadrado'),
        ('M3', 'Metro Cúbico'),
        ('KG', 'Quilograma'),
        ('G', 'Grama'),
        ('LT', 'Litro'),
        ('ML', 'Mililitro'),
        ('CX', 'Caixa'),
        ('PCT', 'Pacote'),
        ('RL', 'Rolo'),
    ]
    unidade = models.CharField(
        max_length=3,
        choices=UNIDADE_CHOICES,
        default='UN',
        verbose_name="Unidade de Medida"
    )

    # --- Fornecedor ---
    fornecedor_preferencial = models.ForeignKey(
        'cadastros.Fornecedor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Fornecedor Preferencial"
    )

    # --- Controle de Estoque ---
    quantidade_atual = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=0,
        verbose_name="Quantidade Atual em Estoque",
        help_text="Calculado automaticamente pelas movimentações."
    )
    estoque_minimo = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Estoque Mínimo",
        help_text="Quantidade mínima para alerta de reposição"
    )
    estoque_maximo = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Estoque Máximo",
        help_text="Quantidade máxima recomendada"
    )

    # --- Custo ---
    custo_medio_ponderado = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Custo Médio Ponderado",
        help_text="Calculado automaticamente baseado nas entradas"
    )
    custo_ultima_compra = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Custo da Última Compra"
    )

    # --- Configurações ---
    controlar_lote = models.BooleanField(
        default=False, 
        verbose_name="Controlar por Lote",
        help_text="Se marcado, será obrigatório informar lote nas movimentações"
    )
    tem_validade = models.BooleanField(
        default=False,
        verbose_name="Possui Validade",
        help_text="Se marcado, será controlada a validade dos lotes"
    )
    
    # --- Outros ---
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")

    class Meta:
        app_label = 'estoque'
        verbose_name = "Matéria-Prima"
        verbose_name_plural = "Matérias-Primas"
        ordering = ['descricao']
        unique_together = ['empresa', 'codigo']
        indexes = [
            models.Index(fields=['empresa', 'ativo']),
            models.Index(fields=['codigo']),
            models.Index(fields=['descricao']),
        ]

    def __str__(self):
        return f"{self.codigo} - {self.descricao}"

    # --- Properties para Cálculos Dinâmicos ---

    @property
    def quantidade_em_estoque(self):
        """Retorna a quantidade atual em estoque do campo desnormalizado."""
        return self.quantidade_atual or Decimal('0.000')

    @property
    def valor_total_em_estoque(self):
        """Calcula o valor total do estoque com base no custo médio"""
        return self.quantidade_em_estoque * self.custo_medio_ponderado

    @property
    def status_estoque(self):
        """Retorna o status do estoque (zerado, baixo, normal, alto)"""
        estoque_atual = self.quantidade_em_estoque
        
        if estoque_atual <= 0:
            return 'zerado'
        elif self.estoque_minimo > 0 and estoque_atual <= self.estoque_minimo:
            return 'baixo'
        elif self.estoque_maximo > 0 and estoque_atual >= self.estoque_maximo:
            return 'alto'
        else:
            return 'normal'

    @property
    def status_estoque_cor(self):
        """Retorna uma cor Bootstrap para o status do estoque"""
        status_cores = {
            'zerado': 'danger',
            'baixo': 'warning', 
            'normal': 'success',
            'alto': 'info',
        }
        return status_cores.get(self.status_estoque, 'secondary')

    @property
    def status_estoque_display(self):
        """Retorna o texto do status para exibição"""
        status_display = {
            'zerado': 'Zerado',
            'baixo': 'Estoque Baixo',
            'normal': 'Normal',
            'alto': 'Estoque Alto',
        }
        return status_display.get(self.status_estoque, 'Indefinido')

    @property
    def necessita_reposicao(self):
        """Verifica se a matéria-prima precisa de reposição"""
        return self.status_estoque in ['zerado', 'baixo']

    # Métodos de negócio foram movidos para a camada de serviço
    # em apps.estoque.services.materia_prima_service 