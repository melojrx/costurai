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


class TipoProduto(TenantBaseModel):
    """
    Tipos de produtos para categorização mais específica
    Ex: Calça, Blusa, Vestido, Shorts, etc.
    """
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, verbose_name="Empresa")
    
    nome = models.CharField(max_length=50, verbose_name="Nome do Tipo")
    descricao = models.TextField(blank=True, verbose_name="Descrição")
    cor_hex = models.CharField(
        max_length=7, 
        default='#3b82f6', 
        verbose_name="Cor",
        help_text="Cor hexadecimal para identificação visual"
    )
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    
    class Meta:
        verbose_name = "Tipo de Produto"
        verbose_name_plural = "Tipos de Produtos"
        ordering = ['nome']
        unique_together = ['empresa', 'nome']
    
    def __str__(self):
        return self.nome


class NCM(TenantBaseModel):
    """
    Nomenclatura Comum do Mercosul para classificação fiscal
    """
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, verbose_name="Empresa")
    
    codigo = models.CharField(max_length=10, verbose_name="Código NCM")
    descricao = models.CharField(max_length=200, verbose_name="Descrição")
    aliquota_ipi = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        verbose_name="Alíquota IPI (%)"
    )
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    
    class Meta:
        verbose_name = "NCM"
        verbose_name_plural = "NCMs"
        ordering = ['codigo']
        unique_together = ['empresa', 'codigo']
    
    def __str__(self):
        return f"{self.codigo} - {self.descricao}"


class TipoGrade(TenantBaseModel):
    """
    Tipos de grade para produtos (Números, Letras, Idade)
    """
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, verbose_name="Empresa")
    
    nome = models.CharField(max_length=50, verbose_name="Nome do Tipo de Grade")
    descricao = models.TextField(blank=True, verbose_name="Descrição")
    
    # Tipos pré-definidos
    TIPO_CHOICES = [
        ('NUMEROS', 'Números (36, 38, 40, 42, etc.)'),
        ('LETRAS', 'Letras (PP, P, M, G, GG, etc.)'),
        ('IDADE', 'Idade (2, 4, 6, 8, 10, etc.)'),
        ('PERSONALIZADO', 'Personalizado'),
    ]
    tipo = models.CharField(
        max_length=15,
        choices=TIPO_CHOICES,
        default='LETRAS',
        verbose_name="Tipo"
    )
    
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    
    class Meta:
        verbose_name = "Tipo de Grade"
        verbose_name_plural = "Tipos de Grades"
        ordering = ['nome']
        unique_together = ['empresa', 'nome']
    
    def __str__(self):
        return self.nome


class ValorGrade(TenantBaseModel):
    """
    Valores específicos de cada tipo de grade
    """
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, verbose_name="Empresa")
    tipo_grade = models.ForeignKey(
        TipoGrade, 
        on_delete=models.CASCADE, 
        related_name='valores',
        verbose_name="Tipo de Grade"
    )
    
    valor = models.CharField(max_length=10, verbose_name="Valor")
    descricao = models.CharField(max_length=50, blank=True, verbose_name="Descrição")
    ordem = models.IntegerField(default=1, verbose_name="Ordem de Exibição")
    ativo = models.BooleanField(default=True, verbose_name="Ativo")
    
    class Meta:
        verbose_name = "Valor de Grade"
        verbose_name_plural = "Valores de Grades"
        ordering = ['tipo_grade', 'ordem', 'valor']
        unique_together = ['tipo_grade', 'valor']
    
    def __str__(self):
        return f"{self.tipo_grade.nome} - {self.valor}"


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
    Modelo de Produto para confecção modernizado:
    - Código automático
    - Sem campos desnecessários (referencia, cor, unidade, consumos)
    - Sistema de grades flexível
    - Classificação NCM
    """
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, verbose_name="Empresa")
    
    # Identificação - Código automático
    codigo = models.CharField(
        max_length=20, 
        verbose_name="Código",
        help_text="Código automático do produto (ex: PR001, PR002, etc.)"
    )
    
    # Classificação
    tipo_produto = models.ForeignKey(
        TipoProduto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Tipo de Produto"
    )
    
    categoria = models.ForeignKey(
        CategoriaProduto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Categoria"
    )
    
    # Descrição
    descricao = models.TextField(verbose_name="Descrição do Produto")
    
    # Classificação fiscal
    ncm = models.ForeignKey(
        NCM,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="NCM"
    )
    
    # Sistema de grades
    tipo_grade = models.ForeignKey(
        TipoGrade,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Tipo de Grade",
        help_text="Define o tipo de grade de tamanhos para este produto"
    )
    
    # Tamanhos disponíveis
    tamanhos = models.ManyToManyField(
        TamanhoProduto,
        through='ProdutoTamanho',
        verbose_name="Tamanhos Disponíveis",
        help_text="Tamanhos em que este produto está disponível"
    )
    
    # Preços
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
    custo_total_materias_primas = models.DecimalField(
        max_digits=10, 
        decimal_places=4, 
        default=0,
        verbose_name="Custo Total de Matérias-Primas",
        help_text="Calculado automaticamente pela ficha técnica do produto."
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
        ordering = ['codigo']
        unique_together = ['empresa', 'codigo']
    
    def __str__(self):
        return f"{self.codigo} - {self.descricao}"
    
    def save(self, *args, **kwargs):
        """Gera código automático se não fornecido"""
        if not self.codigo or self.codigo == 'TEMP':
            self.codigo = self._gerar_codigo_automatico()
        super().save(*args, **kwargs)
    
    def _gerar_codigo_automatico(self):
        """Gera código automático seguindo padrão PR001, PR002, etc."""
        # Buscar o último código usado
        ultimo_produto = Produto.objects.filter(
            empresa=self.empresa,
            codigo__startswith='PR'
        ).order_by('-codigo').first()
        
        if ultimo_produto:
            try:
                # Extrair número do último código (ex: PR001 -> 1)
                ultimo_numero = int(ultimo_produto.codigo.replace('PR', ''))
                proximo_numero = ultimo_numero + 1
            except (ValueError, TypeError):
                # Se não conseguir extrair número, começar do 1
                proximo_numero = 1
        else:
            # Primeiro produto
            proximo_numero = 1
        
        # Gerar código com 3 dígitos (PR001, PR002, etc.)
        novo_codigo = f"PR{proximo_numero:03d}"
        
        # Verificar se código já existe (segurança)
        while Produto.objects.filter(empresa=self.empresa, codigo=novo_codigo).exists():
            proximo_numero += 1
            novo_codigo = f"PR{proximo_numero:03d}"
        
        return novo_codigo
    
    @property
    def nome(self):
        """Propriedade para compatibilidade - retorna código + descrição"""
        return f"{self.codigo} - {self.descricao}"
    
    @property
    def margem_lucro(self):
        """Calcula margem de lucro"""
        if self.preco_venda and self.preco_custo:
            return ((self.preco_venda - self.preco_custo) / self.preco_venda) * 100
        return None

    @property
    def custo_materias_primas(self):
        """Usa o campo desnormalizado para performance."""
        return self.custo_total_materias_primas
    
    @property
    def tamanhos_disponiveis(self):
        """Retorna string com tamanhos disponíveis"""
        return ", ".join([t.codigo for t in self.tamanhos.filter(ativo=True).order_by('ordem')])
    
    def calcular_custo_total(self):
        """Calcula custo total incluindo matérias-primas"""
        custo_materias = self.custo_total_materias_primas
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
        'estoque.MateriaPrima', 
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
        ordering = ['materia_prima__descricao']
    
    def __str__(self):
        return f"{self.produto.nome} - {self.materia_prima.descricao}"
    
    @property
    def custo_total(self):
        """Custo total desta matéria-prima para o produto"""
        return self.quantidade * self.materia_prima.custo_medio_ponderado


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
