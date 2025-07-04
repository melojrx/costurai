from django.contrib import admin
from .models import Cliente, Produto, ProdutoMateriaPrima, ProdutoTamanho, TamanhoProduto, Fornecedor, CategoriaProduto


class ProdutoMateriaPrimaInline(admin.TabularInline):
    model = ProdutoMateriaPrima
    extra = 1
    fields = ('materia_prima', 'quantidade', 'observacoes')


class ProdutoTamanhoInline(admin.TabularInline):
    model = ProdutoTamanho
    extra = 1
    fields = ('tamanho', 'preco_custo_especifico', 'preco_venda_especifico', 'ativo')


@admin.register(TamanhoProduto)
class TamanhoProdutoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'descricao', 'tipo', 'ordem', 'ativo', 'created_at')
    list_filter = ('tipo', 'ativo', 'created_at')
    search_fields = ('codigo', 'descricao')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Dados Básicos', {
            'fields': ('codigo', 'descricao', 'tipo', 'ordem', 'ativo')
        }),
        ('Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'nome_fantasia', 'cnpj', 'cidade', 'estado', 'ativo', 'created_at')
    list_filter = ('ativo', 'estado', 'created_at')
    search_fields = ('nome', 'nome_fantasia', 'cnpj', 'email', 'contato_principal')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Dados Básicos', {
            'fields': ('nome', 'nome_fantasia', 'cnpj', 'inscricao_estadual', 'ativo')
        }),
        ('Endereço', {
            'fields': ('endereco', 'bairro', 'cidade', 'estado', 'cep')
        }),
        ('Contato', {
            'fields': ('contato_principal', 'telefone_comercial', 'telefone_celular', 'email')
        }),
        ('Observações', {
            'fields': ('observacoes',)
        }),
        ('Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'referencia', 'produto', 'cor', 'tamanhos_disponiveis', 'preco_custo', 'preco_venda', 'ativo', 'created_at')
    list_filter = ('produto', 'ativo', 'unidade', 'created_at')
    search_fields = ('codigo', 'referencia', 'descricao', 'cor')
    readonly_fields = ('created_at', 'updated_at', 'margem_lucro', 'consumo_total_linha', 'custo_materias_primas', 'tamanhos_disponiveis')
    inlines = [ProdutoTamanhoInline, ProdutoMateriaPrimaInline]
    
    fieldsets = (
        ('Identificação', {
            'fields': ('codigo', 'referencia', 'produto', 'descricao', 'ativo')
        }),
        ('Características', {
            'fields': ('codigo_cor', 'cor', 'unidade', 'imagem')
        }),
        ('Tamanhos', {
            'fields': ('tamanhos_disponiveis',),
            'description': 'Configure os tamanhos disponíveis na seção abaixo'
        }),
        ('Preços', {
            'fields': ('preco_custo', 'preco_venda', 'margem_lucro')
        }),
        ('Preços Legado', {
            'fields': ('preco_unitario', 'custo_unitario'),
            'classes': ('collapse',)
        }),
        ('Consumo de Linhas', {
            'fields': ('consumo_linha_externa', 'consumo_linha_interna', 'consumo_fio', 'consumo_total_linha')
        }),
        ('Matérias-Primas', {
            'fields': ('custo_materias_primas',),
            'description': 'Custo calculado automaticamente baseado nas matérias-primas associadas'
        }),
        ('Observações', {
            'fields': ('observacoes',)
        }),
        ('Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(ProdutoTamanho)
class ProdutoTamanhoAdmin(admin.ModelAdmin):
    list_display = ('produto', 'tamanho', 'preco_custo_final', 'preco_venda_final', 'ativo')
    list_filter = ('tamanho__tipo', 'ativo', 'produto__produto')
    search_fields = ('produto__codigo', 'produto__referencia', 'tamanho__codigo')
    readonly_fields = ('preco_custo_final', 'preco_venda_final')
    
    fieldsets = (
        ('Produto e Tamanho', {
            'fields': ('produto', 'tamanho', 'ativo')
        }),
        ('Preços Específicos (Opcional)', {
            'fields': ('preco_custo_especifico', 'preco_venda_especifico'),
            'description': 'Se preenchidos, sobrescrevem os preços padrão do produto'
        }),
        ('Preços Finais', {
            'fields': ('preco_custo_final', 'preco_venda_final'),
            'description': 'Preços que serão utilizados (específicos ou padrão do produto)'
        }),
        ('Observações', {
            'fields': ('observacoes',)
        })
    )


@admin.register(ProdutoMateriaPrima)
class ProdutoMateriaPrimaAdmin(admin.ModelAdmin):
    list_display = ('produto', 'materia_prima', 'quantidade', 'custo_total')
    list_filter = ('produto__produto', 'materia_prima__nome')
    search_fields = ('produto__codigo', 'produto__referencia', 'materia_prima__nome')
    readonly_fields = ('custo_total',)


@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ('razao_social', 'nome_fantasia', 'tipo_fornecedor', 'cidade', 'uf', 'ativo', 'created_at')
    list_filter = ('tipo_fornecedor', 'ativo', 'uf', 'created_at')
    search_fields = ('razao_social', 'nome_fantasia', 'cnpj_cpf', 'email', 'contato_principal')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Dados Básicos', {
            'fields': ('razao_social', 'nome_fantasia', 'tipo_fornecedor', 'cnpj_cpf', 'inscricao_estadual', 'ativo')
        }),
        ('Endereço', {
            'fields': ('endereco', 'bairro', 'cidade', 'uf', 'cep')
        }),
        ('Contato', {
            'fields': ('contato_principal', 'telefone', 'email')
        }),
        ('Dados Bancários', {
            'fields': ('banco', 'agencia', 'conta'),
            'classes': ('collapse',)
        }),
        ('Observações', {
            'fields': ('observacoes',)
        }),
        ('Sistema', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(CategoriaProduto)
class CategoriaProdutoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao', 'ativo', 'created_at')
    list_filter = ('ativo', 'created_at')
    search_fields = ('nome', 'descricao')
    readonly_fields = ('created_at', 'updated_at')
