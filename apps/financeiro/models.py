from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from django.utils import timezone
from apps.core.models import TenantBaseModel, Empresa
from apps.producao.models import OrdemProducao
from apps.cadastros.models import Cliente


class StatusPagamento(models.TextChoices):
    """Choices para status de pagamento"""
    PENDENTE = 'PENDENTE', 'Pendente'
    PARCIAL = 'PARCIAL', 'Parcial'
    PAGO = 'PAGO', 'Pago'
    VENCIDO = 'VENCIDO', 'Vencido'
    CANCELADO = 'CANCELADO', 'Cancelado'


class FormaPagamento(models.TextChoices):
    """Choices para forma de pagamento"""
    DINHEIRO = 'DINHEIRO', 'Dinheiro'
    PIX = 'PIX', 'PIX'
    TRANSFERENCIA = 'TRANSFERENCIA', 'Transferência'
    CARTAO_CREDITO = 'CARTAO_CREDITO', 'Cartão de Crédito'
    CARTAO_DEBITO = 'CARTAO_DEBITO', 'Cartão de Débito'
    BOLETO = 'BOLETO', 'Boleto'
    CHEQUE = 'CHEQUE', 'Cheque'


class ContaReceber(TenantBaseModel):
    """
    Modelo para controle de contas a receber
    Baseado na aba de faturamento da planilha do cliente
    """
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, verbose_name="Empresa")
    
    # Relacionamentos
    ordem_producao = models.ForeignKey(
        OrdemProducao, 
        on_delete=models.CASCADE, 
        related_name='contas_receber',
        null=True,
        blank=True,
        verbose_name="Ordem de Produção",
        help_text="Deixe em branco para contas independentes"
    )
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, verbose_name="Cliente")
    
    # Dados da conta
    numero_conta = models.CharField(max_length=20, verbose_name="Número da Conta")
    descricao = models.CharField(max_length=200, verbose_name="Descrição")
    
    # Valores
    valor_total = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        verbose_name="Valor Total"
    )
    valor_recebido = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        verbose_name="Valor Recebido"
    )
    
    # Datas
    data_emissao = models.DateField(verbose_name="Data de Emissão")
    data_vencimento = models.DateField(verbose_name="Data de Vencimento")
    data_recebimento = models.DateField(null=True, blank=True, verbose_name="Data de Recebimento")
    
    # Status e controle
    status = models.CharField(
        max_length=20,
        choices=StatusPagamento.choices,
        default=StatusPagamento.PENDENTE,
        verbose_name="Status"
    )
    
    # Observações
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    
    class Meta:
        verbose_name = "Conta a Receber"
        verbose_name_plural = "Contas a Receber"
        ordering = ['-data_emissao', 'data_vencimento']
        unique_together = ['empresa', 'numero_conta']
    
    def __str__(self):
        return f"{self.numero_conta} - {self.cliente.nome} - R$ {self.valor_total}"
    
    @property
    def valor_pendente(self):
        """Calcula o valor ainda pendente de recebimento"""
        return self.valor_total - self.valor_recebido
    
    @property
    def percentual_recebido(self):
        """Calcula o percentual já recebido"""
        if self.valor_total > 0:
            return (self.valor_recebido / self.valor_total) * 100
        return 0
    
    @property
    def dias_vencimento(self):
        """Calcula quantos dias até o vencimento (negativo se vencido)"""
        return (self.data_vencimento - timezone.now().date()).days
    
    @property
    def esta_vencido(self):
        """Verifica se a conta está vencida"""
        return self.data_vencimento < timezone.now().date() and self.status != StatusPagamento.PAGO
    
    def save(self, *args, **kwargs):
        # Gerar número da conta automaticamente se não fornecido
        if not self.numero_conta:
            ultimo_numero = ContaReceber.objects.filter(
                empresa=self.empresa
            ).aggregate(
                ultimo=models.Max('numero_conta')
            )['ultimo']
            
            if ultimo_numero:
                try:
                    numero = int(ultimo_numero.split('-')[-1]) + 1
                except:
                    numero = 1
            else:
                numero = 1
            
            self.numero_conta = f"CR-{timezone.now().year}-{numero:04d}"
        
        # Atualizar status baseado no valor recebido
        if self.valor_recebido >= self.valor_total:
            self.status = StatusPagamento.PAGO
            if not self.data_recebimento:
                self.data_recebimento = timezone.now().date()
        elif self.valor_recebido > 0:
            self.status = StatusPagamento.PARCIAL
        elif self.esta_vencido:
            self.status = StatusPagamento.VENCIDO
        else:
            self.status = StatusPagamento.PENDENTE
        
        super().save(*args, **kwargs)


class PagamentoRecebido(TenantBaseModel):
    """
    Modelo para registrar pagamentos recebidos
    Permite múltiplos pagamentos para uma conta
    """
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, verbose_name="Empresa")
    
    # Relacionamentos
    conta_receber = models.ForeignKey(
        ContaReceber, 
        on_delete=models.CASCADE, 
        related_name='pagamentos',
        verbose_name="Conta a Receber"
    )
    
    # Dados do pagamento
    valor_pago = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        verbose_name="Valor Pago"
    )
    data_pagamento = models.DateField(verbose_name="Data do Pagamento")
    forma_pagamento = models.CharField(
        max_length=20,
        choices=FormaPagamento.choices,
        verbose_name="Forma de Pagamento"
    )
    
    # Dados bancários (opcional)
    banco = models.CharField(max_length=100, blank=True, verbose_name="Banco")
    agencia = models.CharField(max_length=10, blank=True, verbose_name="Agência")
    conta = models.CharField(max_length=20, blank=True, verbose_name="Conta")
    
    # Controle
    numero_documento = models.CharField(max_length=50, blank=True, verbose_name="Número do Documento")
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    usuario_registro = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="Usuário")
    
    class Meta:
        verbose_name = "Pagamento Recebido"
        verbose_name_plural = "Pagamentos Recebidos"
        ordering = ['-data_pagamento']
    
    def __str__(self):
        return f"Pag. {self.conta_receber.numero_conta} - R$ {self.valor_pago} - {self.data_pagamento}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Atualizar o valor recebido na conta
        self.conta_receber.valor_recebido = self.conta_receber.pagamentos.aggregate(
            total=models.Sum('valor_pago')
        )['total'] or 0
        self.conta_receber.save()


class FaturamentoMensal(TenantBaseModel):
    """
    Modelo para consolidar faturamento mensal
    Baseado na aba 2 da planilha (Relatório de Faturamento)
    """
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, verbose_name="Empresa")
    
    # Período
    mes = models.IntegerField(verbose_name="Mês")
    ano = models.IntegerField(verbose_name="Ano")
    
    # Quantidades (baseado na planilha)
    entradas = models.IntegerField(default=0, verbose_name="Entradas (OPs Cadastradas)")
    saidas = models.IntegerField(default=0, verbose_name="Saídas (OPs Concluídas)")
    a_produzir = models.IntegerField(default=0, verbose_name="A Produzir (OPs em Andamento)")
    
    # Valores financeiros
    valor_entradas = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        verbose_name="Valor das Entradas"
    )
    valor_saidas = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        verbose_name="Valor das Saídas"
    )
    valor_recebido = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        verbose_name="Valor Recebido"
    )
    falta_receber = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        verbose_name="Falta Receber"
    )
    
    # Controle
    data_atualizacao = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")
    
    class Meta:
        verbose_name = "Faturamento Mensal"
        verbose_name_plural = "Faturamentos Mensais"
        ordering = ['-ano', '-mes']
        unique_together = ['empresa', 'mes', 'ano']
    
    def __str__(self):
        return f"Faturamento {self.mes:02d}/{self.ano} - {self.empresa.nome}"
    
    @property
    def periodo_formatado(self):
        """Retorna o período formatado"""
        meses = [
            '', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
        ]
        return f"{meses[self.mes]} de {self.ano}"
    
    @classmethod
    def atualizar_faturamento(cls, empresa, mes, ano):
        """
        Método para atualizar automaticamente o faturamento mensal
        baseado nos dados das OPs e contas a receber
        """
        from apps.producao.models import OrdemProducao, StatusOP
        from django.db.models import Sum
        from datetime import date
        
        # Buscar ou criar o registro de faturamento
        faturamento, created = cls.objects.get_or_create(
            empresa=empresa,
            mes=mes,
            ano=ano
        )
        
        # Calcular entradas (OPs cadastradas no mês)
        entradas = OrdemProducao.objects.filter(
            empresa=empresa,
            data_entrada__month=mes,
            data_entrada__year=ano
        ).count()
        
        # Calcular saídas (OPs concluídas no mês)
        saidas = OrdemProducao.objects.filter(
            empresa=empresa,
            status=StatusOP.CONCLUIDA,
            data_conclusao__month=mes,
            data_conclusao__year=ano
        ).count()
        
        # Calcular a produzir (OPs em andamento)
        a_produzir = OrdemProducao.objects.filter(
            empresa=empresa,
            status__in=[StatusOP.CADASTRADA, StatusOP.EM_PRODUCAO]
        ).count()
        
        # Calcular valores
        valor_entradas = OrdemProducao.objects.filter(
            empresa=empresa,
            data_entrada__month=mes,
            data_entrada__year=ano
        ).aggregate(
            total=Sum('preco_unitario')
        )['total'] or 0
        
        valor_saidas = OrdemProducao.objects.filter(
            empresa=empresa,
            status=StatusOP.CONCLUIDA,
            data_conclusao__month=mes,
            data_conclusao__year=ano
        ).aggregate(
            total=Sum('preco_unitario')
        )['total'] or 0
        
        valor_recebido = PagamentoRecebido.objects.filter(
            empresa=empresa,
            data_pagamento__month=mes,
            data_pagamento__year=ano
        ).aggregate(
            total=Sum('valor_pago')
        )['total'] or 0
        
        # Calcular falta receber (total de contas pendentes)
        falta_receber = ContaReceber.objects.filter(
            empresa=empresa,
            status__in=[StatusPagamento.PENDENTE, StatusPagamento.PARCIAL, StatusPagamento.VENCIDO]
        ).aggregate(
            total=Sum('valor_total') - Sum('valor_recebido')
        )['total'] or 0
        
        # Atualizar o registro
        faturamento.entradas = entradas
        faturamento.saidas = saidas
        faturamento.a_produzir = a_produzir
        faturamento.valor_entradas = valor_entradas
        faturamento.valor_saidas = valor_saidas
        faturamento.valor_recebido = valor_recebido
        faturamento.falta_receber = falta_receber
        faturamento.save()
        
        return faturamento


class CategoriaContaPagar(TenantBaseModel):
    """
    Categorias principais para contas a pagar
    Ex: Despesas Operacionais, Custos de Produção, Despesas Administrativas, etc.
    """
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, verbose_name="Empresa")
    nome = models.CharField(max_length=100, verbose_name="Nome da Categoria")
    descricao = models.TextField(blank=True, verbose_name="Descrição")
    codigo = models.CharField(
        max_length=20, 
        blank=True,
        verbose_name="Código",
        help_text="Código contábil da categoria"
    )
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    
    # Configurações contábeis
    dedutivel = models.BooleanField(
        default=True, 
        verbose_name="Dedutível",
        help_text="Se a despesa é dedutível para fins fiscais"
    )
    centro_custo = models.CharField(
        max_length=50, 
        blank=True,
        verbose_name="Centro de Custo Padrão"
    )
    
    class Meta:
        verbose_name = "Categoria de Conta a Pagar"
        verbose_name_plural = "Categorias de Contas a Pagar"
        ordering = ['nome']
        unique_together = ['empresa', 'nome']
    
    def __str__(self):
        return f"{self.codigo} - {self.nome}" if self.codigo else self.nome


class SubcategoriaContaPagar(TenantBaseModel):
    """
    Subcategorias de contas a pagar
    Ex: Dentro de "Despesas Operacionais": Aluguel, Energia, Água, Internet, etc.
    """
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, verbose_name="Empresa")
    categoria = models.ForeignKey(
        CategoriaContaPagar, 
        on_delete=models.CASCADE, 
        related_name='subcategorias',
        verbose_name="Categoria"
    )
    nome = models.CharField(max_length=100, verbose_name="Nome da Subcategoria")
    descricao = models.TextField(blank=True, verbose_name="Descrição")
    codigo = models.CharField(
        max_length=20, 
        blank=True,
        verbose_name="Código",
        help_text="Código contábil da subcategoria"
    )
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    
    # Configurações específicas
    recorrente = models.BooleanField(
        default=False,
        verbose_name="Despesa Recorrente",
        help_text="Se esta despesa se repete mensalmente"
    )
    dia_vencimento_padrao = models.IntegerField(
        null=True, 
        blank=True,
        verbose_name="Dia de Vencimento Padrão",
        help_text="Dia do mês para vencimento (1-31)"
    )
    
    class Meta:
        verbose_name = "Subcategoria de Conta a Pagar"
        verbose_name_plural = "Subcategorias de Contas a Pagar"
        ordering = ['categoria', 'nome']
        unique_together = ['empresa', 'categoria', 'nome']
    
    def __str__(self):
        return f"{self.categoria.nome} > {self.nome}"


class TipoDocumento(models.TextChoices):
    """Tipos de documento para contas a pagar"""
    NOTA_FISCAL = 'NF', 'Nota Fiscal'
    BOLETO = 'BOL', 'Boleto'
    FATURA = 'FAT', 'Fatura'
    RECIBO = 'REC', 'Recibo'
    CONTRATO = 'CTR', 'Contrato'
    OUTROS = 'OUT', 'Outros'


class StatusContaPagar(models.TextChoices):
    """Status para contas a pagar"""
    PENDENTE = 'PENDENTE', 'Pendente'
    PARCIAL = 'PARCIAL', 'Parcialmente Pago'
    PAGO = 'PAGO', 'Pago'
    VENCIDO = 'VENCIDO', 'Vencido'
    CANCELADO = 'CANCELADO', 'Cancelado'
    AGENDADO = 'AGENDADO', 'Agendado'


class ContaPagar(TenantBaseModel):
    """
    Modelo principal para contas a pagar
    """
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, verbose_name="Empresa")
    
    # Categorização
    categoria = models.ForeignKey(
        CategoriaContaPagar,
        on_delete=models.PROTECT,
        verbose_name="Categoria"
    )
    subcategoria = models.ForeignKey(
        SubcategoriaContaPagar,
        on_delete=models.PROTECT,
        verbose_name="Subcategoria"
    )
    
    # Dados do fornecedor
    fornecedor_nome = models.CharField(max_length=200, verbose_name="Fornecedor")
    fornecedor_documento = models.CharField(
        max_length=20, 
        blank=True,
        verbose_name="CNPJ/CPF do Fornecedor"
    )
    
    # Dados da conta
    numero_documento = models.CharField(
        max_length=50,
        verbose_name="Número do Documento"
    )
    tipo_documento = models.CharField(
        max_length=3,
        choices=TipoDocumento.choices,
        default=TipoDocumento.NOTA_FISCAL,
        verbose_name="Tipo de Documento"
    )
    descricao = models.CharField(max_length=300, verbose_name="Descrição")
    
    # Valores
    valor_original = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Valor Original"
    )
    valor_juros = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Juros/Multa"
    )
    valor_desconto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Desconto"
    )
    valor_pago = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Valor Pago"
    )
    
    # Datas
    data_emissao = models.DateField(verbose_name="Data de Emissão")
    data_vencimento = models.DateField(verbose_name="Data de Vencimento")
    data_pagamento = models.DateField(null=True, blank=True, verbose_name="Data de Pagamento")
    
    # Parcelamento
    parcelado = models.BooleanField(default=False, verbose_name="Parcelado")
    numero_parcelas = models.IntegerField(default=1, verbose_name="Número de Parcelas")
    
    # Status e controle
    status = models.CharField(
        max_length=20,
        choices=StatusContaPagar.choices,
        default=StatusContaPagar.PENDENTE,
        verbose_name="Status"
    )
    
    # Recorrência
    recorrente = models.BooleanField(default=False, verbose_name="Conta Recorrente")
    conta_origem = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='contas_recorrentes',
        verbose_name="Conta Origem",
        help_text="Conta que originou esta conta recorrente"
    )
    
    # Dados bancários para pagamento
    banco_pagamento = models.CharField(max_length=100, blank=True, verbose_name="Banco")
    agencia_pagamento = models.CharField(max_length=10, blank=True, verbose_name="Agência")
    conta_pagamento = models.CharField(max_length=20, blank=True, verbose_name="Conta")
    
    # Centro de custo
    centro_custo = models.CharField(max_length=50, blank=True, verbose_name="Centro de Custo")
    
    # Anexos e observações
    arquivo_documento = models.FileField(
        upload_to='contas_pagar/documentos/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="Arquivo do Documento"
    )
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    
    # Controle
    usuario_criacao = models.ForeignKey(
        User, 
        on_delete=models.PROTECT,
        related_name='contas_pagar_criadas',
        verbose_name="Criado por"
    )
    aprovado_por = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='contas_pagar_aprovadas',
        verbose_name="Aprovado por"
    )
    data_aprovacao = models.DateTimeField(null=True, blank=True, verbose_name="Data de Aprovação")
    
    class Meta:
        verbose_name = "Conta a Pagar"
        verbose_name_plural = "Contas a Pagar"
        ordering = ['data_vencimento', '-data_emissao']
        indexes = [
            models.Index(fields=['empresa', 'status', 'data_vencimento']),
            models.Index(fields=['empresa', 'categoria', 'subcategoria']),
        ]
    
    def __str__(self):
        return f"{self.numero_documento} - {self.fornecedor_nome} - R$ {self.valor_total}"
    
    @property
    def valor_total(self):
        """Calcula o valor total da conta (original + juros - desconto)"""
        return self.valor_original + self.valor_juros - self.valor_desconto
    
    @property
    def valor_pendente(self):
        """Calcula o valor ainda pendente de pagamento"""
        return self.valor_total - self.valor_pago
    
    @property
    def percentual_pago(self):
        """Calcula o percentual já pago"""
        if self.valor_total > 0:
            return (self.valor_pago / self.valor_total) * 100
        return 0
    
    @property
    def dias_vencimento(self):
        """Calcula quantos dias até o vencimento (negativo se vencido)"""
        return (self.data_vencimento - timezone.now().date()).days
    
    @property
    def esta_vencido(self):
        """Verifica se a conta está vencida"""
        return self.data_vencimento < timezone.now().date() and self.status not in [StatusContaPagar.PAGO, StatusContaPagar.CANCELADO]
    
    def save(self, *args, **kwargs):
        # Atualizar status baseado no valor pago
        if self.valor_pago >= self.valor_total:
            self.status = StatusContaPagar.PAGO
            if not self.data_pagamento:
                self.data_pagamento = timezone.now().date()
        elif self.valor_pago > 0:
            self.status = StatusContaPagar.PARCIAL
        elif self.esta_vencido and self.status not in [StatusContaPagar.CANCELADO, StatusContaPagar.AGENDADO]:
            self.status = StatusContaPagar.VENCIDO
        
        # Se não tem centro de custo, pegar da subcategoria
        if not self.centro_custo and self.subcategoria:
            self.centro_custo = self.categoria.centro_custo
        
        super().save(*args, **kwargs)
    
    def gerar_parcelas(self):
        """Gera as parcelas da conta se for parcelada"""
        if not self.parcelado or self.numero_parcelas <= 1:
            return
        
        # Limpar parcelas existentes
        self.parcelas.all().delete()
        
        valor_parcela = self.valor_total / self.numero_parcelas
        data_vencimento = self.data_vencimento
        
        for i in range(self.numero_parcelas):
            ParcelaContaPagar.objects.create(
                empresa=self.empresa,
                conta_pagar=self,
                numero_parcela=i + 1,
                valor=valor_parcela,
                data_vencimento=data_vencimento,
                status=StatusContaPagar.PENDENTE
            )
            
            # Próxima parcela vence no mês seguinte
            if data_vencimento.month == 12:
                data_vencimento = data_vencimento.replace(year=data_vencimento.year + 1, month=1)
            else:
                data_vencimento = data_vencimento.replace(month=data_vencimento.month + 1)


class ParcelaContaPagar(TenantBaseModel):
    """
    Modelo para controlar parcelas de contas a pagar
    """
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, verbose_name="Empresa")
    conta_pagar = models.ForeignKey(
        ContaPagar,
        on_delete=models.CASCADE,
        related_name='parcelas',
        verbose_name="Conta a Pagar"
    )
    
    numero_parcela = models.IntegerField(verbose_name="Número da Parcela")
    valor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Valor da Parcela"
    )
    valor_pago = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Valor Pago"
    )
    
    data_vencimento = models.DateField(verbose_name="Data de Vencimento")
    data_pagamento = models.DateField(null=True, blank=True, verbose_name="Data de Pagamento")
    
    status = models.CharField(
        max_length=20,
        choices=StatusContaPagar.choices,
        default=StatusContaPagar.PENDENTE,
        verbose_name="Status"
    )
    
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    
    class Meta:
        verbose_name = "Parcela de Conta a Pagar"
        verbose_name_plural = "Parcelas de Contas a Pagar"
        ordering = ['conta_pagar', 'numero_parcela']
        unique_together = ['conta_pagar', 'numero_parcela']
    
    def __str__(self):
        return f"{self.conta_pagar.numero_documento} - Parcela {self.numero_parcela}/{self.conta_pagar.numero_parcelas}"
    
    @property
    def valor_pendente(self):
        """Calcula o valor pendente da parcela"""
        return self.valor - self.valor_pago


class PagamentoEfetuado(TenantBaseModel):
    """
    Modelo para registrar pagamentos efetuados
    """
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, verbose_name="Empresa")
    
    # Relacionamento com conta ou parcela
    conta_pagar = models.ForeignKey(
        ContaPagar,
        on_delete=models.CASCADE,
        related_name='pagamentos_efetuados',
        verbose_name="Conta a Pagar"
    )
    parcela = models.ForeignKey(
        ParcelaContaPagar,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='pagamentos',
        verbose_name="Parcela"
    )
    
    # Dados do pagamento
    valor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Valor Pago"
    )
    data_pagamento = models.DateField(verbose_name="Data do Pagamento")
    forma_pagamento = models.CharField(
        max_length=20,
        choices=FormaPagamento.choices,
        verbose_name="Forma de Pagamento"
    )
    
    # Dados bancários
    banco = models.CharField(max_length=100, blank=True, verbose_name="Banco")
    agencia = models.CharField(max_length=10, blank=True, verbose_name="Agência")
    conta = models.CharField(max_length=20, blank=True, verbose_name="Conta")
    numero_transacao = models.CharField(max_length=100, blank=True, verbose_name="Número da Transação")
    
    # Comprovante
    comprovante = models.FileField(
        upload_to='contas_pagar/comprovantes/%Y/%m/',
        blank=True,
        null=True,
        verbose_name="Comprovante de Pagamento"
    )
    
    # Controle
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    usuario_pagamento = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name="Pago por")
    
    class Meta:
        verbose_name = "Pagamento Efetuado"
        verbose_name_plural = "Pagamentos Efetuados"
        ordering = ['-data_pagamento']
    
    def __str__(self):
        return f"Pag. {self.conta_pagar.numero_documento} - R$ {self.valor} - {self.data_pagamento}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Atualizar valor pago na conta
        total_pago = self.conta_pagar.pagamentos_efetuados.aggregate(
            total=models.Sum('valor')
        )['total'] or 0
        
        self.conta_pagar.valor_pago = total_pago
        self.conta_pagar.save()
        
        # Se tem parcela, atualizar também
        if self.parcela:
            parcela_pago = self.parcela.pagamentos.aggregate(
                total=models.Sum('valor')
            )['total'] or 0
            
            self.parcela.valor_pago = parcela_pago
            if parcela_pago >= self.parcela.valor:
                self.parcela.status = StatusContaPagar.PAGO
                self.parcela.data_pagamento = self.data_pagamento
            elif parcela_pago > 0:
                self.parcela.status = StatusContaPagar.PARCIAL
            self.parcela.save()
