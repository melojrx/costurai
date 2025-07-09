from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    MateriaPrima, CategoriaMateriaPrima, MovimentacaoEstoque, 
    InventarioFisico, ItemInventario, LoteMateriaPrima
)


@admin.register(CategoriaMateriaPrima)
class CategoriaMateriaPrimaAdmin(admin.ModelAdmin):
    """Administração de Categorias de Matérias-Primas"""
    list_display = ['nome', 'cor_preview', 'empresa', 'quantidade_materias', 'ativo', 'created_at']
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
    
    def quantidade_materias(self, obj):
        """Mostra quantidade de matérias-primas na categoria"""
        count = obj.materiaprima_set.count()
        if count > 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">{} matérias</span>',
                count
            )
        return format_html('<span style="color: orange;">Nenhuma matéria</span>')
    quantidade_materias.short_description = 'Matérias-Primas'


@admin.register(MateriaPrima)
class MateriaPrimaAdmin(admin.ModelAdmin):
    """Administração de Matérias-Primas"""
    list_display = [
        'codigo', 'descricao', 'categoria', 'unidade', 'quantidade_atual', 
        'status_estoque_display', 'custo_ultima_compra', 'valor_total_display', 
        'ativo', 'empresa'
    ]
    list_filter = [
        'categoria', 'unidade', 'ativo', 'empresa', 'controlar_lote', 
        'tem_validade', 'created_at'
    ]
    search_fields = ['codigo', 'descricao', 'codigo_barras']
    readonly_fields = [
        'created_at', 'updated_at', 'quantidade_atual', 'custo_medio_ponderado',
        'status_estoque_display', 'valor_total_em_estoque'
    ]
    
    fieldsets = (
        ('Identificação', {
            'fields': ('empresa', 'codigo', 'codigo_barras', 'descricao', 'categoria')
        }),
        ('Especificações', {
            'fields': ('unidade', 'fornecedor_preferencial')
        }),
        ('Controle de Estoque', {
            'fields': (
                'quantidade_atual', 'estoque_minimo', 'estoque_maximo',
                'status_estoque_display', 'valor_total_em_estoque'
            )
        }),
        ('Custos', {
            'fields': ('custo_medio_ponderado', 'custo_ultima_compra')
        }),
        ('Configurações Avançadas', {
            'fields': ('controlar_lote', 'tem_validade'),
            'classes': ('collapse',)
        }),
        ('Outros', {
            'fields': ('observacoes', 'ativo')
        }),
        ('Auditoria', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_estoque_display(self, obj):
        """Mostra o status do estoque com cor"""
        status = obj.status_estoque
        cores = {
            'zerado': 'red',
            'baixo': 'orange',
            'normal': 'green',
            'alto': 'blue'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            cores.get(status, 'black'),
            obj.status_estoque_display
        )
    status_estoque_display.short_description = 'Status Estoque'
    
    def valor_total_display(self, obj):
        """Mostra o valor total em estoque"""
        valor = obj.valor_total_em_estoque
        if valor > 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">R$ {:.2f}</span>',
                valor
            )
        return format_html('<span style="color: gray;">R$ 0,00</span>')
    valor_total_display.short_description = 'Valor Total'
    
    def save_model(self, request, obj, form, change):
        """Gera código automático se necessário"""
        if not obj.codigo:
            # Gerar código automático MP001, MP002, etc.
            ultimo = MateriaPrima.objects.filter(
                empresa=obj.empresa,
                codigo__startswith='MP'
            ).order_by('-codigo').first()
            
            if ultimo:
                try:
                    numero = int(ultimo.codigo.replace('MP', '')) + 1
                except:
                    numero = 1
            else:
                numero = 1
            
            obj.codigo = f'MP{numero:03d}'
        
        super().save_model(request, obj, form, change)


@admin.register(MovimentacaoEstoque)
class MovimentacaoEstoqueAdmin(admin.ModelAdmin):
    """Administração de Movimentações de Estoque"""
    list_display = [
        'data_movimento', 'materia_prima', 'get_tipo_movimento_display', 
        'quantidade', 'custo_unitario', 'valor_total', 'numero_documento', 'empresa'
    ]
    list_filter = [
        'tipo_movimento', 'data_movimento', 'empresa', 'cancelada', 'created_at'
    ]
    search_fields = ['materia_prima__descricao', 'numero_documento', 'observacoes']
    readonly_fields = ['created_at', 'updated_at', 'valor_total', 'data_movimento']
    date_hierarchy = 'data_movimento'
    
    fieldsets = (
        ('Movimentação', {
            'fields': (
                'empresa', 'materia_prima', 'tipo_movimento', 
                'data_movimento', 'quantidade'
            )
        }),
        ('Valores', {
            'fields': ('custo_unitario', 'valor_total')
        }),
        ('Documentação', {
            'fields': ('numero_documento', 'observacoes')
        }),
        ('Lote (se aplicável)', {
            'fields': ('lote',),
            'classes': ('collapse',)
        }),
        ('Cancelamento', {
            'fields': ('cancelada', 'data_cancelamento', 'usuario_cancelamento', 'motivo_cancelamento'),
            'classes': ('collapse',)
        }),
        ('Auditoria', {
            'fields': ('created_at', 'updated_at', 'usuario', 'ip_address'),
            'classes': ('collapse',)
        }),
    )


@admin.register(LoteMateriaPrima)
class LoteMateriaPrimaAdmin(admin.ModelAdmin):
    """Administração de Lotes de Matérias-Primas"""
    list_display = [
        'numero_lote', 'materia_prima', 'data_fabricacao', 'data_validade',
        'quantidade_atual', 'status', 'empresa'
    ]
    list_filter = [
        'status', 'data_fabricacao', 'data_validade', 'empresa', 'created_at'
    ]
    search_fields = ['numero_lote', 'materia_prima__descricao']
    readonly_fields = ['created_at', 'updated_at', 'quantidade_atual']
    date_hierarchy = 'data_validade'
    
    fieldsets = (
        ('Identificação', {
            'fields': ('empresa', 'numero_lote', 'materia_prima')
        }),
        ('Datas', {
            'fields': ('data_fabricacao', 'data_validade')
        }),
        ('Estoque', {
            'fields': ('quantidade_inicial', 'quantidade_atual', 'status')
        }),
        ('Outros', {
            'fields': ('observacoes',)
        }),
        ('Auditoria', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(InventarioFisico)
class InventarioFisicoAdmin(admin.ModelAdmin):
    """Administração de Inventários Físicos"""
    list_display = [
        'numero', 'descricao', 'data_inicio', 'data_finalizacao', 'status', 
        'total_itens', 'empresa'
    ]
    list_filter = ['status', 'data_inicio', 'data_finalizacao', 'empresa', 'created_at']
    search_fields = ['numero', 'descricao']
    readonly_fields = ['created_at', 'updated_at', 'total_itens', 'data_abertura']
    date_hierarchy = 'data_inicio'
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('empresa', 'numero', 'descricao', 'responsavel')
        }),
        ('Período', {
            'fields': ('data_abertura', 'data_inicio', 'data_finalizacao')
        }),
        ('Configurações', {
            'fields': ('incluir_zerados', 'categoria_filtro')
        }),
        ('Status', {
            'fields': ('status', 'total_itens')
        }),
        ('Observações', {
            'fields': ('observacoes',)
        }),
        ('Auditoria', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def total_itens(self, obj):
        """Mostra total de itens no inventário"""
        count = obj.itens.count()
        return format_html(
            '<span style="color: blue; font-weight: bold;">{} itens</span>',
            count
        )
    total_itens.short_description = 'Total de Itens'


@admin.register(ItemInventario)
class ItemInventarioAdmin(admin.ModelAdmin):
    """Administração de Itens de Inventário"""
    list_display = [
        'inventario', 'materia_prima', 'quantidade_sistema', 'quantidade_fisica',
        'diferenca_display', 'contado', 'empresa'
    ]
    list_filter = ['contado', 'inventario', 'empresa', 'created_at']
    search_fields = ['materia_prima__descricao', 'inventario__numero']
    readonly_fields = ['created_at', 'updated_at', 'diferenca', 'data_contagem']
    
    fieldsets = (
        ('Inventário', {
            'fields': ('empresa', 'inventario', 'materia_prima')
        }),
        ('Quantidades', {
            'fields': ('quantidade_sistema', 'quantidade_fisica', 'diferenca')
        }),
        ('Controle', {
            'fields': ('contado', 'data_contagem', 'usuario_contagem')
        }),
        ('Custo', {
            'fields': ('custo_unitario',)
        }),
        ('Observações', {
            'fields': ('observacoes',)
        }),
        ('Auditoria', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def diferenca_display(self, obj):
        """Mostra a diferença com cor"""
        diff = obj.diferenca
        if diff > 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">+{:.3f}</span>',
                diff
            )
        elif diff < 0:
            return format_html(
                '<span style="color: red; font-weight: bold;">{:.3f}</span>',
                diff
            )
        return format_html('<span style="color: gray;">0.000</span>')
    diferenca_display.short_description = 'Diferença'


# Configurações globais do admin para estoque
admin.site.site_header = 'CosturAI - Administração'
admin.site.site_title = 'CosturAI Admin'
admin.site.index_title = 'Painel de Administração'
