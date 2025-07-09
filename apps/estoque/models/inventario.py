from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from apps.core.models import TenantBaseModel


class StatusInventario(models.TextChoices):
    """Status do inventário físico"""
    ABERTO = 'ABERTO', 'Aberto'
    EM_ANDAMENTO = 'EM_ANDAMENTO', 'Em Andamento'
    FINALIZADO = 'FINALIZADO', 'Finalizado'
    CANCELADO = 'CANCELADO', 'Cancelado'


class InventarioFisico(TenantBaseModel):
    """
    Representa um evento de contagem de inventário físico.
    """
    empresa = models.ForeignKey(
        'core.Empresa',
        on_delete=models.CASCADE,
        verbose_name="Empresa"
    )
    
    # --- Identificação ---
    numero = models.CharField(
        max_length=20,
        verbose_name="Número do Inventário",
        help_text="Gerado automaticamente"
    )
    descricao = models.CharField(
        max_length=255,
        verbose_name="Descrição",
        help_text="Ex: Inventário Mensal - Janeiro 2024"
    )
    
    # --- Datas ---
    data_abertura = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Abertura"
    )
    data_inicio = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data de Início"
    )
    data_finalizacao = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data de Finalização"
    )
    
    # --- Controle ---
    status = models.CharField(
        max_length=15,
        choices=StatusInventario.choices,
        default=StatusInventario.ABERTO,
        verbose_name="Status"
    )
    responsavel = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name="Responsável"
    )
    
    # --- Configurações ---
    incluir_zerados = models.BooleanField(
        default=False,
        verbose_name="Incluir Itens Zerados",
        help_text="Se marcado, inclui matérias-primas com estoque zerado"
    )
    categoria_filtro = models.ForeignKey(
        'estoque.CategoriaMateriaPrima',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Filtrar por Categoria",
        help_text="Se selecionado, inventário apenas desta categoria"
    )
    
    # --- Observações ---
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações"
    )
    
    class Meta:
        app_label = 'estoque'
        verbose_name = "Inventário Físico"
        verbose_name_plural = "Inventários Físicos"
        ordering = ['-data_abertura']
        unique_together = ['empresa', 'numero']
    
    def __str__(self):
        return f"{self.numero} - {self.descricao}"
    
    @property
    def total_itens(self):
        """Total de itens no inventário"""
        return self.itens.count()
    
    @property
    def itens_contados(self):
        """Itens já contados"""
        return self.itens.filter(contado=True).count()
    
    @property
    def percentual_conclusao(self):
        """Percentual de conclusão do inventário"""
        if self.total_itens == 0:
            return 0
        return (self.itens_contados / self.total_itens) * 100
    
    @property
    def total_diferencas(self):
        """Total de itens com diferenças"""
        return self.itens.filter(
            contado=True
        ).exclude(diferenca=0).count()
    
    def gerar_itens(self):
        """Gera os itens do inventário baseado nos filtros"""
        from .materia_prima import MateriaPrima
        
        # Query base
        materias = MateriaPrima.objects.filter(
            empresa=self.empresa,
            ativo=True
        )
        
        # Aplicar filtros
        if self.categoria_filtro:
            materias = materias.filter(categoria=self.categoria_filtro)
        
        if not self.incluir_zerados:
            # Filtrar apenas com estoque > 0
            materias = [mp for mp in materias if mp.quantidade_em_estoque > 0]
        
        # Criar itens do inventário
        for materia in materias:
            ItemInventario.objects.get_or_create(
                inventario=self,
                materia_prima=materia,
                defaults={
                    'quantidade_sistema': materia.quantidade_em_estoque,
                    'custo_unitario': materia.custo_medio_ponderado
                }
            )
    
    def finalizar(self, gerar_ajustes=True):
        """Finaliza o inventário e gera ajustes se necessário"""
        from django.utils import timezone
        from ..services import EstoqueService
        from .movimentacao import TipoMovimentacao
        
        if self.status != StatusInventario.EM_ANDAMENTO:
            raise ValueError("Inventário deve estar em andamento para ser finalizado")
        
        # Verificar se todos os itens foram contados
        itens_pendentes = self.itens.filter(contado=False)
        if itens_pendentes.exists():
            raise ValueError(f"Ainda há {itens_pendentes.count()} itens não contados")
        
        self.status = StatusInventario.FINALIZADO
        self.data_finalizacao = timezone.now()
        self.save()
        
        # Gerar ajustes automáticos se solicitado
        if gerar_ajustes:
            for item in self.itens.filter(diferenca__ne=0):
                if item.diferenca > 0:
                    # Entrada por inventário
                    EstoqueService.registrar_movimentacao(
                        empresa=self.empresa,
                        materia_prima=item.materia_prima,
                        tipo_movimento=TipoMovimentacao.ENTRADA_INVENTARIO,
                        quantidade=item.diferenca,
                        custo_unitario=item.custo_unitario,
                        origem=self,
                        observacoes=f"Ajuste por inventário {self.numero}"
                    )
                else:
                    # Saída por inventário
                    EstoqueService.registrar_movimentacao(
                        empresa=self.empresa,
                        materia_prima=item.materia_prima,
                        tipo_movimento=TipoMovimentacao.SAIDA_INVENTARIO,
                        quantidade=item.diferenca,
                        custo_unitario=item.custo_unitario,
                        origem=self,
                        observacoes=f"Ajuste por inventário {self.numero}"
                    )


class ItemInventario(TenantBaseModel):
    """
    Um item específico dentro de um inventário físico.
    """
    empresa = models.ForeignKey(
        'core.Empresa',
        on_delete=models.CASCADE,
        verbose_name="Empresa"
    )
    inventario = models.ForeignKey(
        InventarioFisico,
        on_delete=models.CASCADE,
        related_name='itens',
        verbose_name="Inventário"
    )
    materia_prima = models.ForeignKey(
        'estoque.MateriaPrima',
        on_delete=models.PROTECT,
        verbose_name="Matéria-Prima"
    )
    
    # --- Quantidades ---
    quantidade_sistema = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        verbose_name="Quantidade no Sistema",
        help_text="Quantidade registrada no sistema"
    )
    quantidade_fisica = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Quantidade Física",
        help_text="Quantidade contada fisicamente"
    )
    
    # --- Controle ---
    contado = models.BooleanField(
        default=False,
        verbose_name="Contado"
    )
    data_contagem = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Data da Contagem"
    )
    usuario_contagem = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Usuário que Contou"
    )
    
    # --- Custo ---
    custo_unitario = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0,
        verbose_name="Custo Unitário",
        help_text="Custo no momento do inventário"
    )
    
    # --- Observações ---
    observacoes = models.TextField(
        blank=True,
        verbose_name="Observações da Contagem"
    )
    
    class Meta:
        app_label = 'estoque'
        verbose_name = "Item do Inventário"
        verbose_name_plural = "Itens do Inventário"
        ordering = ['materia_prima__descricao']
        unique_together = ['inventario', 'materia_prima']
    
    def __str__(self):
        return f"{self.inventario.numero} - {self.materia_prima.descricao}"
    
    @property
    def diferenca(self):
        """Calcula a diferença entre físico e sistema"""
        return self.quantidade_fisica - self.quantidade_sistema
    
    @property
    def percentual_diferenca(self):
        """Calcula o percentual de diferença"""
        if self.quantidade_sistema == 0:
            return 100 if self.quantidade_fisica > 0 else 0
        return (self.diferenca / self.quantidade_sistema) * 100
    
    @property
    def valor_diferenca(self):
        """Calcula o valor da diferença"""
        return self.diferenca * self.custo_unitario
    
    @property
    def status_diferenca(self):
        """Status da diferença para exibição"""
        diff = self.diferenca
        if diff == 0:
            return 'ok'
        elif diff > 0:
            return 'sobra'
        else:
            return 'falta'
    
    @property
    def cor_diferenca(self):
        """Cor Bootstrap baseada na diferença"""
        status = self.status_diferenca
        cores = {
            'ok': 'success',
            'sobra': 'info',
            'falta': 'warning'
        }
        return cores.get(status, 'secondary')
    
    def marcar_como_contado(self, quantidade_fisica, usuario=None):
        """Marca o item como contado"""
        from django.utils import timezone
        
        self.quantidade_fisica = quantidade_fisica
        self.contado = True
        self.data_contagem = timezone.now()
        self.usuario_contagem = usuario
        self.save() 