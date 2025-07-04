from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from apps.core.models import TenantBaseModel, Empresa
from apps.cadastros.models import Cliente, Produto
from decimal import Decimal


class StatusOP(models.TextChoices):
    """Status das Ordens de Produção - Workflow completo"""
    CADASTRADA = 'CADASTRADA', 'OP Cadastrada'
    PREPARACAO = 'PREPARACAO', 'Preparação'
    FRENTE_EXTERNA = 'FRENTE_EXTERNA', 'Frente Externa'
    MONTAGEM = 'MONTAGEM', 'Montagem'
    EM_PRODUCAO = 'EM_PRODUCAO', 'Em Produção'
    CONCLUIDA = 'CONCLUIDA', 'Concluída'
    FINALIZADA = 'FINALIZADA', 'Finalizada'
    ENTREGUE = 'ENTREGUE', 'Entregue'
    CANCELADA = 'CANCELADA', 'Cancelada'


class StatusEtapa(models.TextChoices):
    """Status das etapas de produção"""
    NAO_INICIADA = 'NAO_INICIADA', 'Não Iniciada'
    EM_ANDAMENTO = 'EM_ANDAMENTO', 'Em Andamento'
    CONCLUIDA = 'CONCLUIDA', 'Concluída'
    PAUSADA = 'PAUSADA', 'Pausada'
    CANCELADA = 'CANCELADA', 'Cancelada'


class StatusLinha(models.TextChoices):
    """Status das linhas de produção"""
    ATIVA = 'ATIVA', 'Ativa'
    PARADA = 'PARADA', 'Parada'
    MANUTENCAO = 'MANUTENCAO', 'Manutenção'
    INATIVA = 'INATIVA', 'Inativa'


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


class LinhaProducao(TenantBaseModel):
    """Linhas de produção da empresa"""
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, verbose_name="Empresa")
    nome = models.CharField(max_length=100, verbose_name="Nome da Linha")
    descricao = models.TextField(blank=True, verbose_name="Descrição")
    capacidade_diaria = models.IntegerField(default=100, verbose_name="Capacidade Diária",
                                          help_text="Número de peças por dia")
    capacidade_horaria = models.IntegerField(default=12, verbose_name="Capacidade Horária",
                                           help_text="Número de peças por hora")
    
    # Status e controle
    status = models.CharField(max_length=20, choices=StatusLinha.choices, 
                            default=StatusLinha.ATIVA, verbose_name="Status")
    
    # Configurações
    horas_trabalho_dia = models.DecimalField(max_digits=4, decimal_places=2, default=8.0,
                                           verbose_name="Horas de Trabalho/Dia")
    dias_trabalho_semana = models.IntegerField(default=5, verbose_name="Dias de Trabalho/Semana")
    
    # Responsável e equipe
    responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='linhas_responsavel', verbose_name="Responsável")
    operadores = models.ManyToManyField(User, blank=True, related_name='linhas_operador',
                                      verbose_name="Operadores")
    
    # Controle de datas
    data_ultima_producao = models.DateTimeField(null=True, blank=True, verbose_name="Última Produção")
    data_proxima_manutencao = models.DateField(null=True, blank=True, verbose_name="Próxima Manutenção")
    
    # Estatísticas
    total_pecas_produzidas = models.IntegerField(default=0, verbose_name="Total de Peças Produzidas")
    eficiencia_media = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                         verbose_name="Eficiência Média (%)")
    
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    
    class Meta:
        verbose_name = "Linha de Produção"
        verbose_name_plural = "Linhas de Produção"
        unique_together = ['empresa', 'nome']
        ordering = ['nome']
    
    def __str__(self):
        return f"{self.nome} - {self.empresa.nome}"
    
    @property
    def status_color(self):
        """Cor baseada no status"""
        colors = {
            'ATIVA': 'success',
            'PARADA': 'danger',
            'MANUTENCAO': 'warning',
            'INATIVA': 'secondary',
        }
        return colors.get(self.status, 'primary')
    
    @property
    def capacidade_mensal(self):
        """Capacidade mensal baseada nos dias de trabalho"""
        semanas_mes = 4.33  # Média de semanas por mês
        return int(self.capacidade_diaria * self.dias_trabalho_semana * semanas_mes)
    
    @property
    def ops_ativas(self):
        """Número de OPs ativas nesta linha"""
        return self.ops_linha.filter(status__in=[StatusOP.CADASTRADA, StatusOP.EM_PRODUCAO]).count()
    
    @property
    def producao_hoje(self):
        """Produção realizada hoje"""
        from django.utils import timezone
        hoje = timezone.now().date()
        return self.historicos_producao.filter(
            data_registro__date=hoje
        ).aggregate(total=models.Sum('quantidade_produzida'))['total'] or 0
    
    @property
    def eficiencia_hoje(self):
        """Eficiência hoje baseada na capacidade"""
        producao = self.producao_hoje
        if self.capacidade_diaria > 0:
            return (producao / self.capacidade_diaria) * 100
        return 0


class EtapaProducao(TenantBaseModel):
    """Etapas do processo produtivo"""
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, verbose_name="Empresa")
    nome = models.CharField(max_length=100, verbose_name="Nome da Etapa")
    descricao = models.TextField(blank=True, verbose_name="Descrição")
    ordem = models.IntegerField(verbose_name="Ordem", help_text="Ordem de execução da etapa")
    
    # Configurações da etapa
    tempo_medio_minutos = models.IntegerField(default=60, verbose_name="Tempo Médio (min)",
                                            help_text="Tempo médio para completar a etapa")
    requer_aprovacao = models.BooleanField(default=False, verbose_name="Requer Aprovação",
                                         help_text="Se marcado, a etapa precisa ser aprovada para avançar")
    
    # Departamento responsável
    departamento = models.ForeignKey(Departamento, on_delete=models.PROTECT, 
                                   verbose_name="Departamento Responsável")
    
    # Configurações visuais
    cor_hex = models.CharField(max_length=7, default='#3b82f6', verbose_name="Cor",
                              help_text="Cor hexadecimal para representar a etapa")
    icone = models.CharField(max_length=50, default='fas fa-cog', verbose_name="Ícone",
                           help_text="Classe do ícone FontAwesome")
    
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    
    class Meta:
        verbose_name = "Etapa de Produção"
        verbose_name_plural = "Etapas de Produção"
        unique_together = ['empresa', 'nome']
        ordering = ['ordem']
    
    def __str__(self):
        return f"{self.ordem}. {self.nome}"
    
    @property
    def proxima_etapa(self):
        """Próxima etapa na sequência"""
        return EtapaProducao.objects.filter(
            empresa=self.empresa,
            ordem__gt=self.ordem,
            ativo=True
        ).first()
    
    @property
    def etapa_anterior(self):
        """Etapa anterior na sequência"""
        return EtapaProducao.objects.filter(
            empresa=self.empresa,
            ordem__lt=self.ordem,
            ativo=True
        ).last()


class MateriaPrima(TenantBaseModel):
    """Catálogo de matérias primas"""
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, verbose_name="Empresa")
    codigo = models.CharField(max_length=20, verbose_name="Código")
    nome = models.CharField(max_length=200, verbose_name="Nome")
    descricao = models.TextField(blank=True, verbose_name="Descrição")
    unidade_medida = models.CharField(max_length=10, verbose_name="Unidade", 
                                    help_text="Ex: metros, kg, unidades")
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=4, verbose_name="Preço Unitário")
    estoque_atual = models.DecimalField(max_digits=10, decimal_places=3, default=0, verbose_name="Estoque Atual")
    estoque_minimo = models.DecimalField(max_digits=10, decimal_places=3, default=0, verbose_name="Estoque Mínimo")
    fornecedor = models.ForeignKey('cadastros.Fornecedor', on_delete=models.SET_NULL, 
                                 null=True, blank=True, verbose_name="Fornecedor Principal")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    
    class Meta:
        verbose_name = "Matéria Prima"
        verbose_name_plural = "Matérias Primas"
        ordering = ['nome']
        unique_together = ['empresa', 'codigo']
    
    def __str__(self):
        return f"{self.codigo} - {self.nome}"
    
    @property
    def status_estoque(self):
        """Status do estoque baseado no mínimo"""
        if self.estoque_atual <= 0:
            return 'zerado'
        elif self.estoque_atual <= self.estoque_minimo:
            return 'baixo'
        else:
            return 'normal'


def proximo_numero_op(empresa_id):
    from django.utils import timezone
    ano_atual = timezone.now().year
    ultima_op = OrdemProducao.objects.filter(
        empresa_id=empresa_id, 
        numero_op__startswith=f'OP-{ano_atual}'
    ).order_by('numero_op').last()
    
    if ultima_op:
        try:
            ultimo_num = int(ultima_op.numero_op.split('-')[-1])
            novo_num = ultimo_num + 1
        except (ValueError, IndexError):
            novo_num = 1
    else:
        novo_num = 1
        
    return f"OP-{ano_atual}-{novo_num:04d}"


class OrdemProducao(TenantBaseModel):
    """Modelo expandido de Ordem de Produção"""
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, verbose_name="Empresa")
    
    # Identificação
    numero_op = models.CharField(max_length=20, verbose_name="Número da OP", unique=True, blank=True)
    op_externa = models.CharField(max_length=50, blank=True, verbose_name="OP Externa")
    
    # Datas
    data_entrada = models.DateField(auto_now_add=True, verbose_name="Data de Entrada")
    data_previsao = models.DateField(verbose_name="Previsão de Entrega")
    data_inicio = models.DateField(blank=True, null=True, verbose_name="Início Produção")
    data_conclusao = models.DateField(blank=True, null=True, verbose_name="Conclusão")
    
    # Produto e cliente
    produto = models.ForeignKey('cadastros.Produto', on_delete=models.PROTECT, verbose_name="Produto", null=True, blank=True)
    cliente = models.ForeignKey('cadastros.Cliente', on_delete=models.PROTECT, verbose_name="Cliente")
    
    # Linha de produção
    linha_producao = models.ForeignKey(LinhaProducao, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='ops_linha', verbose_name="Linha de Produção")
    
    # Valores
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="P. Unit")
    custo_material = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Custo Material")
    
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
    porcentagem_concluida = models.DecimalField(max_digits=5, decimal_places=2, default=0, 
                                              verbose_name="% Concluído")
    
    class Meta:
        verbose_name = "Ordem de Produção"
        verbose_name_plural = "Ordens de Produção"
        ordering = ['-data_entrada', 'numero_op']
        unique_together = ['empresa', 'numero_op']
    
    def save(self, *args, **kwargs):
        if not self.pk and not self.numero_op:
            self.numero_op = proximo_numero_op(self.empresa.id)

        if self.porcentagem_concluida == 100:
            self.status = StatusOP.CONCLUIDA
        elif self.porcentagem_concluida > 0:
            self.status = StatusOP.EM_PRODUCAO
        
        # Se o produto não for nulo, o preço unitário da OP será o do produto.
        if self.produto and self.produto.preco_unitario:
            self.preco_unitario = self.produto.preco_unitario

        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.numero_op} - {self.cliente}"
    
    @property
    def quantidade_total(self):
        """Soma todas as quantidades por tamanho"""
        return sum(item.quantidade for item in self.itens_grade.all())
    
    @property
    def preco_total(self):
        """Calcula preço total baseado na quantidade total"""
        return self.quantidade_total * self.preco_unitario
    
    @property
    def status_color(self):
        """Retorna cor baseada no status"""
        colors = {
            'CADASTRADA': 'danger',
            'EM_PRODUCAO': 'warning',
            'CONCLUIDA': 'success',
            'ENTREGUE': 'info',
            'CANCELADA': 'secondary',
        }
        return colors.get(self.status, 'primary')
    
    @property
    def prioridade_color(self):
        """Cor baseada na prioridade"""
        colors = {1: 'success', 2: 'info', 3: 'warning', 4: 'danger', 5: 'dark'}
        return colors.get(self.prioridade, 'secondary')
    
    @property
    def dias_para_previsao(self):
        """Calcula dias para previsão"""
        from datetime import date
        if self.data_previsao:
            diff = self.data_previsao - date.today()
            return diff.days
        return None
    
    @property
    def status_prazo(self):
        """Status do prazo baseado na previsão"""
        dias = self.dias_para_previsao
        if dias is None:
            return 'normal'
        elif dias < 0:
            return 'atrasado'
        elif dias <= 3:
            return 'urgente'
        else:
            return 'normal'


class GradeProducao(TenantBaseModel):
    """Grade de tamanhos para cada OP"""
    ordem_producao = models.ForeignKey(OrdemProducao, on_delete=models.CASCADE, 
                                     related_name='itens_grade', verbose_name="Ordem de Produção")
    tamanho = models.CharField(max_length=20, verbose_name="Tamanho")
    quantidade = models.IntegerField(validators=[MinValueValidator(0)], verbose_name="Quantidade")
    quantidade_produzida = models.IntegerField(default=0, validators=[MinValueValidator(0)], 
                                             verbose_name="Quantidade Produzida")
    
    class Meta:
        verbose_name = "Grade de Produção"
        verbose_name_plural = "Grades de Produção"
        unique_together = ['ordem_producao', 'tamanho']
        ordering = ['id']
    
    def __str__(self):
        return f"{self.ordem_producao.numero_op} - {self.tamanho}: {self.quantidade}"
    
    @property
    def porcentagem_concluida(self):
        """Porcentagem produzida para este tamanho"""
        if self.quantidade > 0:
            return (self.quantidade_produzida / self.quantidade) * 100
        return 0


class ConsumoMateriaPrima(TenantBaseModel):
    """Matérias primas necessárias para cada OP"""
    ordem_producao = models.ForeignKey(OrdemProducao, on_delete=models.CASCADE, 
                                     related_name='materias_primas', verbose_name="Ordem de Produção")
    materia_prima = models.ForeignKey(MateriaPrima, on_delete=models.PROTECT, verbose_name="Matéria Prima")
    departamento = models.ForeignKey(Departamento, on_delete=models.PROTECT, verbose_name="Departamento")
    quantidade_necessaria = models.DecimalField(max_digits=10, decimal_places=3, 
                                              verbose_name="Quantidade Necessária")
    quantidade_utilizada = models.DecimalField(max_digits=10, decimal_places=3, default=0, 
                                             verbose_name="Quantidade Utilizada")
    custo_unitario = models.DecimalField(max_digits=10, decimal_places=4, verbose_name="Custo Unitário")
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    
    class Meta:
        verbose_name = "Consumo de Matéria Prima"
        verbose_name_plural = "Consumos de Matéria Prima"
        unique_together = ['ordem_producao', 'materia_prima', 'departamento']
        ordering = ['departamento__ordem', 'materia_prima__nome']
    
    def save(self, *args, **kwargs):
        # Usar preço atual da matéria prima se não especificado
        if not self.custo_unitario:
            self.custo_unitario = self.materia_prima.preco_unitario
        super().save(*args, **kwargs)
    
    @property
    def custo_total(self):
        """Custo total para esta matéria prima"""
        return self.quantidade_necessaria * self.custo_unitario
    
    @property
    def porcentagem_utilizada(self):
        """Porcentagem utilizada da matéria prima"""
        if self.quantidade_necessaria > 0:
            return (self.quantidade_utilizada / self.quantidade_necessaria) * 100
        return 0
    
    def __str__(self):
        return f"{self.ordem_producao.numero_op} - {self.materia_prima.nome}"


class ProcessoProducao(TenantBaseModel):
    """Controle de processos por departamento"""
    ordem_producao = models.ForeignKey(OrdemProducao, on_delete=models.CASCADE, 
                                     related_name='processos', verbose_name="Ordem de Produção")
    departamento = models.ForeignKey(Departamento, on_delete=models.PROTECT, verbose_name="Departamento")
    data_inicio = models.DateTimeField(null=True, blank=True, verbose_name="Data Início")
    data_conclusao = models.DateTimeField(null=True, blank=True, verbose_name="Data Conclusão")
    responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                  verbose_name="Responsável")
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    porcentagem_concluida = models.DecimalField(max_digits=5, decimal_places=2, default=0, 
                                              verbose_name="% Concluído")
    
    class Meta:
        verbose_name = "Processo de Produção"
        verbose_name_plural = "Processos de Produção"
        unique_together = ['ordem_producao', 'departamento']
        ordering = ['departamento__ordem']
    
    @property
    def status(self):
        """Status baseado na porcentagem"""
        if self.porcentagem_concluida == 0:
            return 'nao_iniciado'
        elif self.porcentagem_concluida < 100:
            return 'em_andamento'
        else:
            return 'concluido'
    
    def __str__(self):
        return f"{self.ordem_producao.numero_op} - {self.departamento.nome}"


class HistoricoProducao(TenantBaseModel):
    """Histórico de produção por OP e etapa"""
    ordem_producao = models.ForeignKey(OrdemProducao, on_delete=models.CASCADE,
                                     related_name='historicos_producao', verbose_name="Ordem de Produção")
    linha_producao = models.ForeignKey(LinhaProducao, on_delete=models.CASCADE,
                                     related_name='historicos_producao', verbose_name="Linha de Produção")
    etapa = models.ForeignKey(EtapaProducao, on_delete=models.CASCADE, verbose_name="Etapa")
    
    # Dados da produção
    status_anterior = models.CharField(max_length=20, choices=StatusEtapa.choices,
                                     verbose_name="Status Anterior")
    status_atual = models.CharField(max_length=20, choices=StatusEtapa.choices,
                                  verbose_name="Status Atual")
    
    # Quantidades
    quantidade_produzida = models.IntegerField(default=0, verbose_name="Quantidade Produzida")
    quantidade_defeituosa = models.IntegerField(default=0, verbose_name="Quantidade Defeituosa")
    quantidade_retrabalho = models.IntegerField(default=0, verbose_name="Quantidade Retrabalho")
    
    # Controle de tempo
    data_inicio = models.DateTimeField(verbose_name="Data/Hora Início")
    data_fim = models.DateTimeField(null=True, blank=True, verbose_name="Data/Hora Fim")
    tempo_producao_minutos = models.IntegerField(default=0, verbose_name="Tempo Produção (min)")
    
    # Responsável
    operador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                               verbose_name="Operador")
    supervisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='supervisoes_producao', verbose_name="Supervisor")
    
    # Observações e qualidade
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    problemas_encontrados = models.TextField(blank=True, verbose_name="Problemas Encontrados")
    aprovado = models.BooleanField(default=True, verbose_name="Aprovado")
    aprovado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='aprovacoes_producao', verbose_name="Aprovado Por")
    data_aprovacao = models.DateTimeField(null=True, blank=True, verbose_name="Data Aprovação")
    
    # Dados automáticos
    data_registro = models.DateTimeField(auto_now_add=True, verbose_name="Data de Registro")
    
    class Meta:
        verbose_name = "Histórico de Produção"
        verbose_name_plural = "Históricos de Produção"
        ordering = ['-data_registro']
    
    def save(self, *args, **kwargs):
        # Calcular tempo de produção automaticamente
        if self.data_inicio and self.data_fim:
            delta = self.data_fim - self.data_inicio
            self.tempo_producao_minutos = int(delta.total_seconds() / 60)
        
        super().save(*args, **kwargs)
        
        # Atualizar estatísticas da linha
        if self.linha_producao:
            self.linha_producao.data_ultima_producao = self.data_registro
            self.linha_producao.save()
    
    def __str__(self):
        return f"{self.ordem_producao.numero_op} - {self.etapa.nome} - {self.data_registro.strftime('%d/%m/%Y %H:%M')}"
    
    @property
    def eficiencia(self):
        """Eficiência baseada no tempo médio da etapa"""
        if self.etapa.tempo_medio_minutos > 0 and self.tempo_producao_minutos > 0:
            return (self.etapa.tempo_medio_minutos / self.tempo_producao_minutos) * 100
        return 0
    
    @property
    def quantidade_total(self):
        """Quantidade total trabalhada (produzida + defeituosa + retrabalho)"""
        return self.quantidade_produzida + self.quantidade_defeituosa + self.quantidade_retrabalho


class ControleEtapaOP(TenantBaseModel):
    """Controle de etapas por OP"""
    ordem_producao = models.ForeignKey(OrdemProducao, on_delete=models.CASCADE,
                                     related_name='controles_etapa', verbose_name="Ordem de Produção")
    etapa = models.ForeignKey(EtapaProducao, on_delete=models.CASCADE, verbose_name="Etapa")
    linha_producao = models.ForeignKey(LinhaProducao, on_delete=models.CASCADE,
                                     verbose_name="Linha de Produção")
    
    # Status da etapa para esta OP
    status = models.CharField(max_length=20, choices=StatusEtapa.choices,
                            default=StatusEtapa.NAO_INICIADA, verbose_name="Status")
    
    # Controle de progresso
    porcentagem_concluida = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                              verbose_name="% Concluída")
    quantidade_planejada = models.IntegerField(verbose_name="Quantidade Planejada")
    quantidade_produzida = models.IntegerField(default=0, verbose_name="Quantidade Produzida")
    
    # Datas de controle
    data_inicio = models.DateTimeField(null=True, blank=True, verbose_name="Data Início")
    data_fim = models.DateTimeField(null=True, blank=True, verbose_name="Data Fim")
    data_prevista = models.DateTimeField(null=True, blank=True, verbose_name="Data Prevista")
    
    # Responsável
    responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                  verbose_name="Responsável")
    
    # Observações
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    
    class Meta:
        verbose_name = "Controle de Etapa OP"
        verbose_name_plural = "Controles de Etapa OP"
        unique_together = ['ordem_producao', 'etapa']
        ordering = ['etapa__ordem']
    
    def __str__(self):
        return f"{self.ordem_producao.numero_op} - {self.etapa.nome}"
    
    @property
    def status_color(self):
        """Cor baseada no status"""
        colors = {
            'NAO_INICIADA': 'secondary',
            'EM_ANDAMENTO': 'warning',
            'CONCLUIDA': 'success',
            'PAUSADA': 'info',
            'CANCELADA': 'danger',
        }
        return colors.get(self.status, 'primary')
    
    @property
    def esta_atrasada(self):
        """Verifica se a etapa está atrasada"""
        if self.data_prevista and self.status != StatusEtapa.CONCLUIDA:
            from django.utils import timezone
            return timezone.now() > self.data_prevista
        return False
    
    def iniciar_etapa(self, usuario=None):
        """Inicia a etapa"""
        from django.utils import timezone
        
        if self.status == StatusEtapa.NAO_INICIADA:
            self.status = StatusEtapa.EM_ANDAMENTO
            self.data_inicio = timezone.now()
            if usuario:
                self.responsavel = usuario
            self.save()
            
            # Registrar no histórico
            HistoricoProducao.objects.create(
                ordem_producao=self.ordem_producao,
                linha_producao=self.linha_producao,
                etapa=self.etapa,
                status_anterior=StatusEtapa.NAO_INICIADA,
                status_atual=StatusEtapa.EM_ANDAMENTO,
                data_inicio=self.data_inicio,
                operador=usuario
            )
    
    def concluir_etapa(self, quantidade_produzida=None, usuario=None):
        """Conclui a etapa"""
        from django.utils import timezone
        
        if self.status == StatusEtapa.EM_ANDAMENTO:
            self.status = StatusEtapa.CONCLUIDA
            self.data_fim = timezone.now()
            self.porcentagem_concluida = 100
            
            if quantidade_produzida:
                self.quantidade_produzida = quantidade_produzida
            
            self.save()
            
            # Registrar no histórico
            HistoricoProducao.objects.create(
                ordem_producao=self.ordem_producao,
                linha_producao=self.linha_producao,
                etapa=self.etapa,
                status_anterior=StatusEtapa.EM_ANDAMENTO,
                status_atual=StatusEtapa.CONCLUIDA,
                data_inicio=self.data_inicio,
                data_fim=self.data_fim,
                quantidade_produzida=self.quantidade_produzida,
                operador=usuario
            )
            
            # Verificar se é a última etapa e finalizar a OP
            self._verificar_conclusao_op()
    
    def _verificar_conclusao_op(self):
        """Verifica se todas as etapas foram concluídas para finalizar a OP"""
        from django.utils import timezone
        
        etapas_op = ControleEtapaOP.objects.filter(ordem_producao=self.ordem_producao)
        etapas_concluidas = etapas_op.filter(status=StatusEtapa.CONCLUIDA).count()
        
        if etapas_concluidas == etapas_op.count():
            # Todas as etapas concluídas, finalizar OP
            self.ordem_producao.status = StatusOP.CONCLUIDA
            self.ordem_producao.data_conclusao = timezone.now().date()
            self.ordem_producao.porcentagem_concluida = 100
            self.ordem_producao.save()
            
            # Criar conta a receber automaticamente
            self._criar_conta_receber()
    
    def _criar_conta_receber(self):
        """Cria conta a receber quando OP é finalizada"""
        try:
            from apps.financeiro.models import ContaReceber
            from django.utils import timezone
            
            # Verificar se já existe conta para esta OP
            conta_existente = ContaReceber.objects.filter(
                ordem_producao=self.ordem_producao
            ).exists()
            
            if not conta_existente:
                # Calcular data de vencimento (30 dias após conclusão)
                data_vencimento = timezone.now().date() + timezone.timedelta(days=30)
                
                ContaReceber.objects.create(
                    empresa=self.ordem_producao.empresa,
                    ordem_producao=self.ordem_producao,
                    cliente=self.ordem_producao.cliente,
                    descricao=f"Produção OP {self.ordem_producao.numero_op} - {self.ordem_producao.produto.referencia if self.ordem_producao.produto else 'Produto'}",
                    valor_total=self.ordem_producao.preco_total,
                    data_emissao=timezone.now().date(),
                    data_vencimento=data_vencimento,
                    status='PENDENTE'
                )
                
                # Log da criação da conta
                print(f"✅ Conta a receber criada automaticamente para OP {self.ordem_producao.numero_op}")
                
        except ImportError:
            # Módulo financeiro não disponível
            print("⚠️ Módulo financeiro não disponível para criar conta a receber")
            pass
        except Exception as e:
            # Erro na criação da conta
            print(f"❌ Erro ao criar conta a receber: {str(e)}")
            pass


class CapacidadeProducao(TenantBaseModel):
    """Capacidade produtiva da empresa"""
    empresa = models.OneToOneField(Empresa, on_delete=models.CASCADE, 
                                 related_name='capacidade_producao')
    capacidade_diaria = models.IntegerField(default=300, verbose_name="Capacidade Diária",
                                          help_text="Quantidade de peças que podem ser produzidas por dia")
    capacidade_mensal = models.IntegerField(blank=True, null=True, verbose_name="Capacidade Mensal")
    data_atualizacao = models.DateField(auto_now=True, verbose_name="Data de Atualização")
    
    class Meta:
        verbose_name = "Capacidade de Produção"
        verbose_name_plural = "Capacidades de Produção"
    
    def save(self, *args, **kwargs):
        if not self.capacidade_mensal:
            self.capacidade_mensal = self.capacidade_diaria * 22
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.empresa.nome} - {self.capacidade_diaria}/dia"


class RelatorioFaturamento(models.Model):
    """Relatório consolidado de faturamento"""
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    mes = models.IntegerField(verbose_name="Mês")
    ano = models.IntegerField(verbose_name="Ano")
    
    # Dados de produção
    entradas = models.IntegerField(default=0, verbose_name="Entradas")
    saidas = models.IntegerField(default=0, verbose_name="Saídas")
    a_produzir = models.IntegerField(default=0, verbose_name="A Produzir")
    
    # Valores financeiros
    valor_entradas = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    valor_saidas = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    valor_recebido = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    falta_receber = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    data_geracao = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Relatório de Faturamento"
        verbose_name_plural = "Relatórios de Faturamento"
        unique_together = ['empresa', 'mes', 'ano']
        ordering = ['-ano', '-mes']
    
    def __str__(self):
        return f"{self.empresa.nome} - {self.mes:02d}/{self.ano}"
