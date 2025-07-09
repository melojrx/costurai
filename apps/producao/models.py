from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from apps.core.models import TenantBaseModel, Empresa
from apps.cadastros.models import Cliente, Produto
from decimal import Decimal


class StatusOP(models.TextChoices):
    """Status simplificado para Ordens de Produção"""
    CADASTRADA = 'CADASTRADA', 'Cadastrada'
    EM_PRODUCAO = 'EM_PRODUCAO', 'Em Produção'
    CONCLUIDA = 'CONCLUIDA', 'Concluída'
    CANCELADA = 'CANCELADA', 'Cancelada'


class Departamento(TenantBaseModel):
    """Departamentos da produção (Corte, Costura, Acabamento, etc.)"""
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, verbose_name="Empresa")
    nome = models.CharField(max_length=100, verbose_name="Nome do Departamento")
    descricao = models.TextField(blank=True, verbose_name="Descrição")
    ordem = models.IntegerField(default=1, verbose_name="Ordem do Processo")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    
    class Meta:
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"
        ordering = ['ordem', 'nome']
        unique_together = ['empresa', 'nome']
    
    def __str__(self):
        return self.nome


class OrdemProducao(TenantBaseModel):
    """Modelo Simplificado de Ordem de Produção focado no cadastro."""
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, verbose_name="Empresa")
    
    # Identificação
    numero_op = models.CharField(max_length=20, verbose_name="Número da OP", unique=True, blank=True)
    op_externa = models.CharField(max_length=50, blank=True, verbose_name="OP Externa")
    
    # Datas
    data_entrada = models.DateField(auto_now_add=True, verbose_name="Data de Entrada")
    data_previsao = models.DateField(verbose_name="Previsão de Entrega")
    data_conclusao = models.DateField(blank=True, null=True, verbose_name="Conclusão")
    
    # Produto e cliente
    produto = models.ForeignKey('cadastros.Produto', on_delete=models.PROTECT, verbose_name="Produto", null=True, blank=True)
    cliente = models.ForeignKey('cadastros.Cliente', on_delete=models.PROTECT, verbose_name="Cliente")
    
    # Valores
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="P. Unit")
    
    # Status e controle
    status = models.CharField(max_length=20, choices=StatusOP.choices, 
                            default=StatusOP.CADASTRADA, verbose_name="Status")
    prioridade = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(5)], 
                                   verbose_name="Prioridade", help_text="1=Baixa, 5=Urgente")
    
    # Responsável e observações
    responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                  verbose_name="Responsável")
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    
    # Dados de produção
    quantidade_total = models.IntegerField(
        default=0, 
        verbose_name="Quantidade Total de Peças",
        help_text="Calculado automaticamente pela grade de produção."
    )
    
    class Meta:
        verbose_name = "Ordem de Produção"
        verbose_name_plural = "Ordens de Produção"
        ordering = ['-data_entrada', 'numero_op']
        unique_together = ['empresa', 'numero_op']
    
    def save(self, *args, **kwargs):
        from . import services
        if not self.pk and not self.numero_op:
            self.numero_op = services.gerar_proximo_numero_op(self.empresa.id)

        # Se o produto não for nulo, o preço unitário da OP será o do produto.
        if self.produto and self.produto.preco_unitario:
            self.preco_unitario = self.produto.preco_unitario

        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.numero_op} - {self.cliente}"
    
    @property
    def preco_total(self):
        """Calcula preço total baseado na quantidade total (campo desnormalizado)"""
        return self.quantidade_total * self.preco_unitario
    
    @property
    def status_color(self):
        """Retorna cor baseada no status"""
        colors = {
            'CADASTRADA': 'danger',
            'EM_PRODUCAO': 'warning',
            'CONCLUIDA': 'success',
            'CANCELADA': 'secondary',
        }
        return colors.get(self.status, 'primary')
    

class GradeProducao(TenantBaseModel):
    """Grade de tamanhos para cada OP"""
    ordem_producao = models.ForeignKey(OrdemProducao, on_delete=models.CASCADE, 
                                     related_name='itens_grade', verbose_name="Ordem de Produção")
    tamanho = models.CharField(max_length=20, verbose_name="Tamanho")
    quantidade = models.IntegerField(validators=[MinValueValidator(0)], verbose_name="Quantidade")
    
    class Meta:
        verbose_name = "Grade de Produção"
        verbose_name_plural = "Grades de Produção"
        unique_together = ['ordem_producao', 'tamanho']
        ordering = ['id']
    
    def __str__(self):
        return f"{self.ordem_producao.numero_op} - {self.tamanho}: {self.quantidade}"


class ConsumoMateriaPrima(TenantBaseModel):
    """Matérias primas necessárias para cada OP (Ficha Técnica da OP)"""
    ordem_producao = models.ForeignKey(OrdemProducao, on_delete=models.CASCADE, 
                                     related_name='materias_primas', verbose_name="Ordem de Produção")
    materia_prima = models.ForeignKey('estoque.MateriaPrima', on_delete=models.PROTECT, verbose_name="Matéria Prima")
    quantidade_necessaria = models.DecimalField(max_digits=10, decimal_places=3, 
                                              verbose_name="Quantidade Necessária")
    
    class Meta:
        verbose_name = "Consumo de Matéria Prima"
        verbose_name_plural = "Consumos de Matéria Prima"
        unique_together = ['ordem_producao', 'materia_prima']
        ordering = ['materia_prima__descricao']
    
    def __str__(self):
        return f"{self.ordem_producao.numero_op} - {self.materia_prima.descricao}"
