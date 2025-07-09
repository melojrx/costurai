from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Cliente, CategoriaProduto, TipoProduto, NCM, TipoGrade, ValorGrade,
    TamanhoProduto, Produto, ProdutoTamanho, ProdutoMateriaPrima, Fornecedor
)


class ValorGradeInline(admin.TabularInline):
    """Inline para valores de grade"""
    model = ValorGrade
    extra = 1
    fields = ['valor', 'descricao', 'ordem', 'ativo']
    ordering = ['ordem', 'valor']


@admin.register(TipoGrade)
class TipoGradeAdmin(admin.ModelAdmin):
    """Administração de Tipos de Grade"""
    list_display = ['nome', 'tipo', 'empresa', 'quantidade_valores', 'ativo', 'created_at']
    list_filter = ['tipo', 'ativo', 'empresa', 'created_at']
    search_fields = ['nome', 'descricao']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ValorGradeInline]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('empresa', 'nome', 'tipo', 'descricao')
        }),
        ('Status', {
            'fields': ('ativo',)
        }),
        ('Auditoria', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def quantidade_valores(self, obj):
        """Mostra quantidade de valores cadastrados"""
        count = obj.valores.count()
        if count > 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">{} valores</span>',
                count
            )
        return format_html('<span style="color: orange;">Nenhum valor</span>')
    quantidade_valores.short_description = 'Valores Cadastrados'
    
    def get_queryset(self, request):
        """Filtra por empresa se não for superusuário"""
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            # Aqui você pode implementar filtro por empresa do usuário
            pass
        return qs


@admin.register(ValorGrade)
class ValorGradeAdmin(admin.ModelAdmin):
    """Administração de Valores de Grade"""
    list_display = ['tipo_grade', 'valor', 'descricao', 'ordem', 'ativo']
    list_filter = ['tipo_grade', 'ativo', 'empresa']
    search_fields = ['valor', 'descricao', 'tipo_grade__nome']
    list_editable = ['ordem', 'ativo']
    ordering = ['tipo_grade', 'ordem', 'valor']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('empresa', 'tipo_grade', 'valor', 'descricao')
        }),
        ('Configurações', {
            'fields': ('ordem', 'ativo')
        }),
    )


@admin.register(TamanhoProduto)
class TamanhoProdutoAdmin(admin.ModelAdmin):
    """Administração de Tamanhos de Produtos"""
    list_display = ['codigo', 'descricao', 'tipo', 'ordem', 'ativo', 'empresa']
    list_filter = ['tipo', 'ativo', 'empresa']
    search_fields = ['codigo', 'descricao']
    list_editable = ['ordem', 'ativo']
    ordering = ['tipo', 'ordem', 'codigo']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('empresa', 'tipo', 'codigo', 'descricao')
        }),
        ('Configurações', {
            'fields': ('ordem', 'ativo')
        }),
    )


@admin.register(CategoriaProduto)
class CategoriaProdutoAdmin(admin.ModelAdmin):
    """Administração de Categorias de Produtos"""
    list_display = ['nome', 'empresa', 'ativo', 'created_at']
    list_filter = ['ativo', 'empresa', 'created_at']
    search_fields = ['nome', 'descricao']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('empresa', 'nome', 'descricao')
        }),
        ('Status', {
            'fields': ('ativo',)
        }),
        ('Auditoria', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TipoProduto)
class TipoProdutoAdmin(admin.ModelAdmin):
    """Administração de Tipos de Produtos"""
    list_display = ['nome', 'cor_preview', 'empresa', 'ativo', 'created_at']
    list_filter = ['ativo', 'empresa', 'created_at']
    search_fields = ['nome', 'descricao']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('empresa', 'nome', 'descricao', 'cor_hex')
        }),
        ('Status', {
            'fields': ('ativo',)
        }),
        ('Auditoria', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def cor_preview(self, obj):
        """Mostra preview da cor"""
        return format_html(
            '<div style="width: 20px; height: 20px; background-color: {}; border: 1px solid #ccc; border-radius: 3px; display: inline-block;"></div> {}',
            obj.cor_hex,
            obj.cor_hex
        )
    cor_preview.short_description = 'Cor'


@admin.register(NCM)
class NCMAdmin(admin.ModelAdmin):
    """Administração de NCMs"""
    list_display = ['codigo', 'descricao', 'aliquota_ipi', 'empresa', 'ativo']
    list_filter = ['ativo', 'empresa', 'aliquota_ipi']
    search_fields = ['codigo', 'descricao']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('empresa', 'codigo', 'descricao')
        }),
        ('Configurações Fiscais', {
            'fields': ('aliquota_ipi',)
        }),
        ('Status', {
            'fields': ('ativo',)
        }),
    )


class ProdutoTamanhoInline(admin.TabularInline):
    """Inline para tamanhos do produto"""
    model = ProdutoTamanho
    extra = 1
    fields = ['tamanho', 'preco_custo_especifico', 'preco_venda_especifico', 'ativo']


class ProdutoMateriaPrimaInline(admin.TabularInline):
    """Inline para matérias-primas do produto"""
    model = ProdutoMateriaPrima
    extra = 1
    fields = ['materia_prima', 'quantidade', 'observacoes']
    readonly_fields = ['custo_total_display']
    
    def custo_total_display(self, obj):
        """Mostra o custo total da matéria-prima"""
        if obj.id:
            return format_html(
                '<span style="color: green; font-weight: bold;">R$ {:.2f}</span>',
                obj.custo_total
            )
        return '-'
    custo_total_display.short_description = 'Custo Total'


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    """Administração de Produtos"""
    list_display = ['codigo', 'descricao', 'tipo_produto', 'categoria', 'preco_custo', 'preco_venda', 'margem_display', 'ativo', 'empresa']
    list_filter = ['tipo_produto', 'categoria', 'ativo', 'empresa', 'created_at']
    search_fields = ['codigo', 'descricao']
    readonly_fields = ['created_at', 'updated_at', 'custo_total_materias_primas']
    inlines = [ProdutoTamanhoInline, ProdutoMateriaPrimaInline]
    
    fieldsets = (
        ('Identificação', {
            'fields': ('empresa', 'codigo', 'descricao')
        }),
        ('Classificação', {
            'fields': ('tipo_produto', 'categoria', 'ncm', 'tipo_grade')
        }),
        ('Preços', {
            'fields': ('preco_custo', 'preco_venda', 'custo_total_materias_primas')
        }),
        ('Mídia', {
            'fields': ('imagem',)
        }),
        ('Configurações', {
            'fields': ('ativo', 'observacoes')
        }),
        ('Auditoria', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def margem_display(self, obj):
        """Mostra a margem de lucro"""
        margem = obj.margem_lucro
        if margem is not None:
            cor = 'green' if margem > 0 else 'red'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
                cor, margem
            )
        return '-'
    margem_display.short_description = 'Margem'
    
    def save_model(self, request, obj, form, change):
        """Gera código automático se necessário"""
        if not obj.codigo or obj.codigo == 'TEMP':
            obj.codigo = obj._gerar_codigo_automatico()
        super().save_model(request, obj, form, change)


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    """Administração de Clientes"""
    list_display = ['nome', 'nome_fantasia', 'cnpj', 'cidade', 'contato_principal', 'ativo', 'empresa']
    list_filter = ['ativo', 'estado', 'empresa', 'created_at']
    search_fields = ['nome', 'nome_fantasia', 'cnpj', 'contato_principal']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Dados Básicos', {
            'fields': ('empresa', 'nome', 'nome_fantasia')
        }),
        ('Documentos', {
            'fields': ('cnpj', 'inscricao_estadual')
        }),
        ('Endereço', {
            'fields': ('endereco', 'bairro', 'cidade', 'estado', 'cep')
        }),
        ('Contatos', {
            'fields': ('contato_principal', 'telefone_comercial', 'telefone_celular', 'email')
        }),
        ('Configurações', {
            'fields': ('ativo', 'observacoes')
        }),
        ('Auditoria', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    """Administração de Fornecedores"""
    list_display = ['razao_social', 'nome_fantasia', 'tipo_fornecedor', 'cnpj_cpf', 'cidade', 'contato_principal', 'ativo', 'empresa']
    list_filter = ['tipo_fornecedor', 'ativo', 'uf', 'empresa', 'created_at']
    search_fields = ['razao_social', 'nome_fantasia', 'cnpj_cpf', 'contato_principal']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Dados Básicos', {
            'fields': ('empresa', 'razao_social', 'nome_fantasia', 'tipo_fornecedor')
        }),
        ('Documentos', {
            'fields': ('cnpj_cpf', 'inscricao_estadual')
        }),
        ('Endereço', {
            'fields': ('endereco', 'bairro', 'cidade', 'uf', 'cep')
        }),
        ('Contatos', {
            'fields': ('contato_principal', 'telefone', 'email')
        }),
        ('Dados Bancários', {
            'fields': ('banco', 'agencia', 'conta'),
            'classes': ('collapse',)
        }),
        ('Configurações', {
            'fields': ('ativo', 'observacoes')
        }),
        ('Auditoria', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# Configurações globais do admin
admin.site.site_header = 'CosturAI - Administração'
admin.site.site_title = 'CosturAI Admin'
admin.site.index_title = 'Painel de Administração' 