from django.db import models
from apps.core.models import TenantBaseModel, Empresa


class Cliente(TenantBaseModel):
    """
    Modelo de Cliente baseado nos clientes da planilha:
    - momo confeccoes
    - Blackout  
    - D'Vimme jeans
    """
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, verbose_name="Empresa")
    
    # Dados básicos
    nome = models.CharField(max_length=100, verbose_name="Nome/Razão Social")
    nome_fantasia = models.CharField(max_length=100, blank=True, verbose_name="Nome Fantasia")
    
    # Documentos
    cnpj = models.CharField(max_length=18, blank=True, verbose_name="CNPJ")
    inscricao_estadual = models.CharField(max_length=20, blank=True, verbose_name="Inscrição Estadual")
    
    # Endereço
    endereco = models.TextField(verbose_name="Endereço")
    bairro = models.CharField(max_length=50, verbose_name="Bairro")
    cidade = models.CharField(max_length=50, verbose_name="Cidade")
    estado = models.CharField(max_length=2, verbose_name="Estado")
    cep = models.CharField(max_length=10, verbose_name="CEP")
    
    # Contatos
    contato_principal = models.CharField(max_length=100, verbose_name="Contato Principal")
    telefone_comercial = models.CharField(max_length=20, blank=True, verbose_name="Telefone Comercial")
    telefone_celular = models.CharField(max_length=20, blank=True, verbose_name="Telefone Celular")
    email = models.EmailField(blank=True, verbose_name="E-mail")
    
    # Status
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    
    # Configurações comerciais
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['nome']
        unique_together = ['empresa', 'cnpj']
    
    def __str__(self):
        return self.nome


class CategoriaProduto(TenantBaseModel):
    """
    Categorias de produtos baseadas na planilha:
    - Calça
    - Cigarrete
    - Outros
    """
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, verbose_name="Empresa")
    
    nome = models.CharField(max_length=50, verbose_name="Nome da Categoria")
    descricao = models.TextField(blank=True, verbose_name="Descrição")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    
    class Meta:
        verbose_name = "Categoria de Produto"
        verbose_name_plural = "Categorias de Produtos"
        ordering = ['nome']
        unique_together = ['empresa', 'nome']
    
    def __str__(self):
        return self.nome


class TamanhoProduto(TenantBaseModel):
    """
    Tamanhos flexíveis para produtos
    Permite nomenclaturas personalizadas por empresa
    """
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, verbose_name="Empresa")
    
    # Tipo de tamanho
    TIPO_TAMANHO_CHOICES = [
        ('ADULTO', 'Adulto (P, M, G, etc.)'),
        ('NUMERICO', 'Numérico (36, 38, 40, etc.)'),
        ('INFANTIL', 'Infantil por idade (4, 6, 8, etc.)'),
        ('PERSONALIZADO', 'Personalizado'),
    ]
    tipo = models.CharField(
        max_length=15,
        choices=TIPO_TAMANHO_CHOICES,
        default='ADULTO',
        verbose_name="Tipo de Tamanho"
    )
    
    # Nomenclatura do tamanho
    codigo = models.CharField(
        max_length=10, 
        verbose_name="Código",
        help_text="Ex: P, M, G, 36, 38, 4, 6, etc."
    )
    descricao = models.CharField(
        max_length=50, 
        verbose_name="Descrição",
        help_text="Ex: Pequeno, Médio, Grande, 36 anos, etc."
    )
    
    # Ordem de exibição
    ordem = models.IntegerField(
        default=1, 
        verbose_name="Ordem",
        help_text="Ordem de exibição (menor = primeiro)"
    )
    
    # Status
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    
    class Meta:
        verbose_name = "Tamanho de Produto"
        verbose_name_plural = "Tamanhos de Produtos"
        ordering = ['tipo', 'ordem', 'codigo']
        unique_together = ['empresa', 'codigo']
    
    def __str__(self):
        return f"{self.codigo} - {self.descricao}"


class Produto(TenantBaseModel):
    """
    Modelo de Produto para confecção:
    - Calça, shorts, saia, etc
    - Com controle de consumo de linha e materiais
    - Preços de custo e venda
    - Tamanhos flexíveis
    """
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, verbose_name="Empresa")
    
    # Identificação
    codigo = models.CharField(max_length=20, verbose_name="Código", default='TEMP')
    referencia = models.CharField(max_length=50, verbose_name="Referência")
    
    # Tipo de produto
    TIPO_PRODUTO_CHOICES = [
        ('CALCA', 'Calça'),
        ('SHORTS', 'Shorts'),
        ('SAIA', 'Saia'),
        ('VESTIDO', 'Vestido'),
        ('BLUSA', 'Blusa'),
        ('CAMISA', 'Camisa'),
        ('JAQUETA', 'Jaqueta'),
        ('OUTROS', 'Outros'),
    ]
    produto = models.CharField(
        max_length=10,
        choices=TIPO_PRODUTO_CHOICES,
        default='OUTROS',
        verbose_name="Tipo de Produto"
    )
    
    # Descrição
    descricao = models.TextField(verbose_name="Descrição do Produto", default='Produto sem descrição')
    
    # Consumo de linha
    consumo_linha_externa = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=0,
        verbose_name="Consumo Linha Externa (Metros)"
    )
    consumo_linha_interna = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=0,
        verbose_name="Consumo Linha Interna (metros)"
    )
    consumo_fio = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        default=0,
        verbose_name="Consumo Fio (Kg)"
    )
    
    # Cor
    codigo_cor = models.CharField(max_length=10, verbose_name="Código da Cor", default='00000')
    cor = models.CharField(max_length=50, verbose_name="Nome da Cor", default='Sem cor definida')
    
    # Unidade
    UNIDADE_CHOICES = [
        ('PC', 'Peça'),
        ('KG', 'Quilograma'),
        ('MT', 'Metro'),
        ('UN', 'Unidade'),
    ]
    unidade = models.CharField(
        max_length=2,
        choices=UNIDADE_CHOICES,
        default='PC',
        verbose_name="Unidade"
    )
    
    # Tamanhos disponíveis - NOVO
    tamanhos = models.ManyToManyField(
        TamanhoProduto,
        through='ProdutoTamanho',
        verbose_name="Tamanhos Disponíveis",
        help_text="Tamanhos em que este produto está disponível"
    )
    
    # Preços - NOVO: Separando custo e venda
    preco_custo = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True,
        null=True,
        verbose_name="Preço de Custo",
        help_text="Custo para produzir o produto"
    )
    preco_venda = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True,
        null=True,
        verbose_name="Preço de Venda",
        help_text="Preço de venda do produto"
    )
    
    # Campos antigos mantidos para compatibilidade
    preco_unitario = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True,
        null=True,
        verbose_name="Preço Unitário (Legado)"
    )
    custo_unitario = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True, 
        null=True,
        verbose_name="Custo Unitário (Legado)"
    )
    
    # Imagem
    imagem = models.ImageField(
        upload_to='produtos/', 
        blank=True, 
        null=True, 
        verbose_name="Imagem do Produto"
    )
    
    # Status
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    
    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"
        ordering = ['codigo', 'referencia']
        unique_together = ['empresa', 'codigo']
    
    def __str__(self):
        return f"{self.codigo} - {self.referencia}"
    
    @property
    def nome(self):
        """Propriedade para compatibilidade - retorna código + referência"""
        return f"{self.codigo} - {self.referencia}"
    
    @property
    def margem_lucro(self):
        """Calcula margem de lucro baseada nos novos campos"""
        if self.preco_venda and self.preco_custo:
            return ((self.preco_venda - self.preco_custo) / self.preco_venda) * 100
        # Fallback para campos antigos
        elif self.preco_unitario and self.custo_unitario:
            return ((self.preco_unitario - self.custo_unitario) / self.preco_unitario) * 100
        return None
    
    @property
    def consumo_total_linha(self):
        """Calcula o consumo total de linha"""
        return self.consumo_linha_externa + self.consumo_linha_interna + self.consumo_fio
    
    @property
    def custo_materias_primas(self):
        """Calcula custo total das matérias-primas"""
        return sum(
            item.quantidade * item.materia_prima.preco_unitario 
            for item in self.materias_primas.all()
        )
    
    @property
    def tamanhos_disponiveis(self):
        """Retorna string com tamanhos disponíveis"""
        return ", ".join([t.codigo for t in self.tamanhos.filter(ativo=True).order_by('ordem')])
    
    def calcular_custo_total(self):
        """Calcula custo total incluindo matérias-primas"""
        custo_materias = self.custo_materias_primas
        custo_base = self.preco_custo or 0
        return custo_base + custo_materias


class ProdutoTamanho(TenantBaseModel):
    """
    Relacionamento entre Produto e Tamanho
    Permite configurar preços específicos por tamanho se necessário
    """
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, verbose_name="Empresa")
    produto = models.ForeignKey(
        Produto, 
        on_delete=models.CASCADE, 
        verbose_name="Produto"
    )
    tamanho = models.ForeignKey(
        TamanhoProduto, 
        on_delete=models.CASCADE, 
        verbose_name="Tamanho"
    )
    
    # Preços específicos por tamanho (opcional)
    preco_custo_especifico = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True,
        null=True,
        verbose_name="Preço de Custo Específico",
        help_text="Se preenchido, sobrescreve o preço padrão do produto para este tamanho"
    )
    preco_venda_especifico = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        blank=True,
        null=True,
        verbose_name="Preço de Venda Específico",
        help_text="Se preenchido, sobrescreve o preço padrão do produto para este tamanho"
    )
    
    # Status
    ativo = models.BooleanField(default=True, verbose_name="Disponível")
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    
    class Meta:
        verbose_name = "Produto por Tamanho"
        verbose_name_plural = "Produtos por Tamanho"
        unique_together = ['produto', 'tamanho']
        ordering = ['tamanho__ordem']
    
    def __str__(self):
        return f"{self.produto.codigo} - {self.tamanho.codigo}"
    
    @property
    def preco_custo_final(self):
        """Retorna preço de custo específico ou padrão do produto"""
        return self.preco_custo_especifico or self.produto.preco_custo
    
    @property
    def preco_venda_final(self):
        """Retorna preço de venda específico ou padrão do produto"""
        return self.preco_venda_especifico or self.produto.preco_venda


class ProdutoMateriaPrima(TenantBaseModel):
    """
    Relacionamento entre Produto e Matéria-Prima
    Define quais matérias-primas são usadas em cada produto e suas quantidades
    """
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, verbose_name="Empresa")
    produto = models.ForeignKey(
        Produto, 
        on_delete=models.CASCADE, 
        related_name='materias_primas',
        verbose_name="Produto"
    )
    materia_prima = models.ForeignKey(
        'producao.MateriaPrima', 
        on_delete=models.CASCADE, 
        verbose_name="Matéria-Prima"
    )
    quantidade = models.DecimalField(
        max_digits=10, 
        decimal_places=4, 
        verbose_name="Quantidade Necessária",
        help_text="Quantidade da matéria-prima necessária para produzir 1 unidade do produto"
    )
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    
    class Meta:
        verbose_name = "Matéria-Prima do Produto"
        verbose_name_plural = "Matérias-Primas do Produto"
        unique_together = ['produto', 'materia_prima']
        ordering = ['materia_prima__nome']
    
    def __str__(self):
        return f"{self.produto.nome} - {self.materia_prima.nome}"
    
    @property
    def custo_total(self):
        """Custo total desta matéria-prima para o produto"""
        return self.quantidade * self.materia_prima.preco_unitario


class Fornecedor(TenantBaseModel):
    """
    Modelo de Fornecedor para faccionistas e fornecedores de matéria-prima
    """
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, verbose_name="Empresa")
    
    # Dados básicos
    razao_social = models.CharField(max_length=150, verbose_name="Razão Social")
    nome_fantasia = models.CharField(max_length=100, blank=True, verbose_name="Nome Fantasia")
    
    # Tipo de fornecedor
    TIPO_CHOICES = [
        ('FACCAO', 'Facção'),
        ('MATERIA_PRIMA', 'Matéria Prima'),
        ('AVIAMENTOS', 'Aviamentos'),
        ('SERVICOS', 'Serviços'),
        ('OUTROS', 'Outros'),
    ]
    tipo_fornecedor = models.CharField(
        max_length=15, 
        choices=TIPO_CHOICES, 
        default='FACCAO',
        verbose_name="Tipo de Fornecedor"
    )
    
    # Documentos
    cnpj_cpf = models.CharField(max_length=18, verbose_name="CNPJ/CPF")
    inscricao_estadual = models.CharField(max_length=20, blank=True, verbose_name="Inscrição Estadual")
    
    # Endereço
    endereco = models.TextField(verbose_name="Endereço")
    bairro = models.CharField(max_length=50, verbose_name="Bairro")
    cidade = models.CharField(max_length=50, verbose_name="Cidade")
    uf = models.CharField(max_length=2, verbose_name="UF")
    cep = models.CharField(max_length=10, verbose_name="CEP")
    
    # Contatos
    contato_principal = models.CharField(max_length=100, verbose_name="Contato Principal")
    telefone = models.CharField(max_length=20, verbose_name="Telefone")
    email = models.EmailField(blank=True, verbose_name="E-mail")
    
    # Dados bancários
    banco = models.CharField(max_length=100, blank=True, verbose_name="Banco")
    agencia = models.CharField(max_length=10, blank=True, verbose_name="Agência")
    conta = models.CharField(max_length=20, blank=True, verbose_name="Conta")
    
    # Status
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    observacoes = models.TextField(blank=True, verbose_name="Observações")
    
    class Meta:
        verbose_name = "Fornecedor"
        verbose_name_plural = "Fornecedores"
        ordering = ['razao_social']
        unique_together = ['empresa', 'cnpj_cpf']
    
    def __str__(self):
        return self.nome_fantasia or self.razao_social
