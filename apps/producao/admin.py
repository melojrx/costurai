from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    OrdemProducao, GradeProducao, Departamento, MateriaPrima,
    ConsumoMateriaPrima, ProcessoProducao, CapacidadeProducao,
    RelatorioFaturamento
)


@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'ordem', 'ativo', 'empresa', 'created_at']
    list_filter = ['ativo', 'empresa', 'created_at']
    search_fields = ['nome', 'descricao']
    ordering = ['ordem', 'nome']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'descricao', 'ordem', 'ativo')
        }),
        ('Sistema', {
            'fields': ('empresa',),
            'classes': ('collapse',)
        })
    )


@admin.register(MateriaPrima)
class MateriaPrimaAdmin(admin.ModelAdmin):
    list_display = [
        'codigo', 'nome', 'unidade_medida', 'preco_unitario', 
        'estoque_atual', 'status_estoque_badge', 'ativo', 'empresa'
    ]
    list_filter = ['ativo', 'fornecedor', 'empresa', 'created_at']
    search_fields = ['codigo', 'nome', 'descricao']
    ordering = ['nome']
    
    fieldsets = (
        ('Identificação', {
            'fields': ('codigo', 'nome', 'descricao')
        }),
        ('Especificações', {
            'fields': ('unidade_medida', 'preco_unitario')
        }),
        ('Estoque', {
            'fields': ('estoque_atual', 'estoque_minimo')
        }),
        ('Fornecimento', {
            'fields': ('fornecedor', 'ativo')
        }),
        ('Sistema', {
            'fields': ('empresa',),
            'classes': ('collapse',)
        })
    )
    
    def status_estoque_badge(self, obj):
        status = obj.status_estoque
        colors = {
            'zerado': 'red',
            'baixo': 'orange',
            'normal': 'green'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(status, 'black'),
            status.title()
        )
    status_estoque_badge.short_description = 'Status Estoque'


class GradeProducaoInline(admin.TabularInline):
    model = GradeProducao
    extra = 0
    fields = ['tamanho', 'quantidade', 'quantidade_produzida']
    readonly_fields = ['porcentagem_concluida']
    
    def porcentagem_concluida(self, obj):
        if obj.id:
            return f"{obj.porcentagem_concluida:.1f}%"
        return "-"


class ConsumoMateriaPrimaInline(admin.TabularInline):
    model = ConsumoMateriaPrima
    extra = 0
    fields = [
        'materia_prima', 'departamento', 'quantidade_necessaria', 
        'quantidade_utilizada', 'custo_unitario'
    ]
    readonly_fields = ['custo_total']
    
    def custo_total(self, obj):
        if obj.id:
            return f"R$ {obj.custo_total:.2f}"
        return "-"


class ProcessoProducaoInline(admin.TabularInline):
    model = ProcessoProducao
    extra = 0
    fields = [
        'departamento', 'data_inicio', 'data_conclusao', 
        'porcentagem_concluida', 'responsavel'
    ]
    readonly_fields = ['status_badge']
    
    def status_badge(self, obj):
        if obj.id:
            status = obj.status
            colors = {
                'nao_iniciado': 'gray',
                'em_andamento': 'orange',
                'concluido': 'green'
            }
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}</span>',
                colors.get(status, 'black'),
                status.replace('_', ' ').title()
            )
        return "-"
    status_badge.short_description = 'Status'


@admin.register(OrdemProducao)
class OrdemProducaoAdmin(admin.ModelAdmin):
    list_display = [
        'numero_op', 'cliente', 'produto',
        'status_badge', 'prioridade_badge', 'quantidade_total_display',
        'preco_total_display', 'data_entrada', 'data_previsao'
    ]
    list_filter = [
        'status', 'prioridade', 'data_entrada', 
        'data_previsao', 'empresa', 'created_at'
    ]
    search_fields = [
        'numero_op', 'op_externa', 
        'cliente__nome', 'produto__nome'
    ]
    ordering = ['-data_entrada', 'numero_op']
    
    fieldsets = (
        ('Identificação', {
            'fields': ('numero_op', 'op_externa')
        }),
        ('Produto e Cliente', {
            'fields': ('produto', 'cliente')
        }),
        ('Datas', {
            'fields': ('data_entrada', 'data_previsao', 'data_inicio', 'data_conclusao')
        }),
        ('Valores', {
            'fields': ('preco_unitario', 'custo_material')
        }),
        ('Controle', {
            'fields': ('status', 'prioridade', 'porcentagem_concluida', 'responsavel')
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ('collapse',)
        }),
        ('Sistema', {
            'fields': ('empresa',),
            'classes': ('collapse',)
        })
    )
    
    inlines = [GradeProducaoInline, ConsumoMateriaPrimaInline, ProcessoProducaoInline]
    
    def status_badge(self, obj):
        colors = {
            'CADASTRADA': 'red',
            'EM_PRODUCAO': 'orange',
            'CONCLUIDA': 'green',
            'ENTREGUE': 'blue',
            'CANCELADA': 'gray'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def prioridade_badge(self, obj):
        colors = {1: 'green', 2: 'blue', 3: 'orange', 4: 'red', 5: 'darkred'}
        return format_html(
            '<span style="color: {}; font-weight: bold;">⭐{}</span>',
            colors.get(obj.prioridade, 'black'),
            obj.prioridade
        )
    prioridade_badge.short_description = 'Prioridade'
    
    def quantidade_total_display(self, obj):
        total = obj.quantidade_total
        return f"{total} pç" if total else "0 pç"
    quantidade_total_display.short_description = 'Qtd Total'
    
    def preco_total_display(self, obj):
        total = obj.preco_total
        return f"R$ {total:,.2f}" if total else "R$ 0,00"
    preco_total_display.short_description = 'Valor Total'
    
    def view_on_site(self, obj):
        url = reverse('producao:op_detalhes', args=[obj.pk])
        return url


@admin.register(GradeProducao)
class GradeProducaoAdmin(admin.ModelAdmin):
    list_display = [
        'ordem_producao', 'tamanho', 'quantidade', 
        'quantidade_produzida', 'porcentagem_display'
    ]
    list_filter = ['tamanho', 'ordem_producao__status']
    search_fields = ['ordem_producao__numero_op', 'ordem_producao__cliente__nome']
    ordering = ['ordem_producao', 'tamanho']
    
    def porcentagem_display(self, obj):
        porcentagem = obj.porcentagem_concluida
        color = 'green' if porcentagem == 100 else 'orange' if porcentagem > 0 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color,
            porcentagem
        )
    porcentagem_display.short_description = '% Concluído'


@admin.register(ConsumoMateriaPrima)
class ConsumoMateriaPrimaAdmin(admin.ModelAdmin):
    list_display = [
        'ordem_producao', 'materia_prima', 'departamento',
        'quantidade_necessaria', 'quantidade_utilizada', 
        'custo_total_display', 'porcentagem_utilizada_display'
    ]
    list_filter = [
        'departamento', 'materia_prima__empresa', 
        'ordem_producao__status'
    ]
    search_fields = [
        'ordem_producao__numero_op', 'materia_prima__nome',
        'departamento__nome'
    ]
    ordering = ['ordem_producao', 'departamento__ordem']
    
    def custo_total_display(self, obj):
        return f"R$ {obj.custo_total:,.2f}"
    custo_total_display.short_description = 'Custo Total'
    
    def porcentagem_utilizada_display(self, obj):
        porcentagem = obj.porcentagem_utilizada
        color = 'green' if porcentagem == 100 else 'orange' if porcentagem > 0 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color,
            porcentagem
        )
    porcentagem_utilizada_display.short_description = '% Utilizado'


@admin.register(ProcessoProducao)
class ProcessoProducaoAdmin(admin.ModelAdmin):
    list_display = [
        'ordem_producao', 'departamento', 'responsavel',
        'data_inicio', 'data_conclusao', 'porcentagem_concluida',
        'status_badge'
    ]
    list_filter = [
        'departamento', 'responsavel', 'ordem_producao__status'
    ]
    search_fields = [
        'ordem_producao__numero_op', 'departamento__nome',
        'responsavel__username'
    ]
    ordering = ['ordem_producao', 'departamento__ordem']
    
    def status_badge(self, obj):
        status = obj.status
        colors = {
            'nao_iniciado': 'gray',
            'em_andamento': 'orange',
            'concluido': 'green'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(status, 'black'),
            status.replace('_', ' ').title()
        )
    status_badge.short_description = 'Status'


@admin.register(CapacidadeProducao)
class CapacidadeProducaoAdmin(admin.ModelAdmin):
    list_display = [
        'empresa', 'capacidade_diaria', 'capacidade_mensal', 
        'data_atualizacao'
    ]
    list_filter = ['empresa', 'data_atualizacao']
    ordering = ['empresa']
    
    fieldsets = (
        ('Capacidade', {
            'fields': ('capacidade_diaria', 'capacidade_mensal')
        }),
        ('Sistema', {
            'fields': ('empresa', 'data_atualizacao'),
            'classes': ('collapse',)
        })
    )
    readonly_fields = ['data_atualizacao']


@admin.register(RelatorioFaturamento)
class RelatorioFaturamentoAdmin(admin.ModelAdmin):
    list_display = [
        'empresa', 'mes', 'ano', 'entradas', 'saidas', 
        'valor_entradas_display', 'valor_saidas_display', 'data_geracao'
    ]
    list_filter = ['empresa', 'ano', 'mes', 'data_geracao']
    ordering = ['-ano', '-mes', 'empresa']
    
    fieldsets = (
        ('Período', {
            'fields': ('mes', 'ano')
        }),
        ('Produção', {
            'fields': ('entradas', 'saidas', 'a_produzir')
        }),
        ('Financeiro', {
            'fields': (
                'valor_entradas', 'valor_saidas', 
                'valor_recebido', 'falta_receber'
            )
        }),
        ('Sistema', {
            'fields': ('empresa', 'data_geracao'),
            'classes': ('collapse',)
        })
    )
    readonly_fields = ['data_geracao']
    
    def valor_entradas_display(self, obj):
        return f"R$ {obj.valor_entradas:,.2f}"
    valor_entradas_display.short_description = 'Valor Entradas'
    
    def valor_saidas_display(self, obj):
        return f"R$ {obj.valor_saidas:,.2f}"
    valor_saidas_display.short_description = 'Valor Saídas'


# Configurações globais do admin
admin.site.site_header = "costurai.com.br - Administração"
admin.site.site_title = "costurai.com.br Admin"
admin.site.index_title = "Painel Administrativo"
