from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import ContaReceber, PagamentoRecebido, FaturamentoMensal, StatusPagamento


@admin.register(ContaReceber)
class ContaReceberAdmin(admin.ModelAdmin):
    list_display = [
        'numero_conta', 'cliente', 'valor_total', 'valor_recebido', 
        'valor_pendente_display', 'status_display', 'data_vencimento', 
        'dias_vencimento_display'
    ]
    list_filter = ['status', 'data_vencimento', 'data_emissao', 'empresa']
    search_fields = ['numero_conta', 'cliente__nome', 'ordem_producao__numero_op']
    readonly_fields = ['numero_conta', 'valor_recebido', 'data_recebimento']
    date_hierarchy = 'data_vencimento'
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('numero_conta', 'ordem_producao', 'cliente', 'descricao')
        }),
        ('Valores', {
            'fields': ('valor_total', 'valor_recebido', 'status')
        }),
        ('Datas', {
            'fields': ('data_emissao', 'data_vencimento', 'data_recebimento')
        }),
        ('Observações', {
            'fields': ('observacoes',),
            'classes': ('collapse',)
        })
    )
    
    def valor_pendente_display(self, obj):
        valor = obj.valor_pendente
        if valor > 0:
            color = 'red' if obj.esta_vencido else 'orange'
            return format_html(
                '<span style="color: {};">R$ {:.2f}</span>',
                color, valor
            )
        return format_html('<span style="color: green;">R$ 0,00</span>')
    valor_pendente_display.short_description = 'Valor Pendente'
    
    def status_display(self, obj):
        colors = {
            StatusPagamento.PAGO: 'green',
            StatusPagamento.PENDENTE: 'orange',
            StatusPagamento.PARCIAL: 'blue',
            StatusPagamento.VENCIDO: 'red',
            StatusPagamento.CANCELADO: 'gray'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def dias_vencimento_display(self, obj):
        dias = obj.dias_vencimento
        if dias < 0:
            return format_html(
                '<span style="color: red; font-weight: bold;">{} dias vencido</span>',
                abs(dias)
            )
        elif dias <= 7:
            return format_html(
                '<span style="color: orange; font-weight: bold;">Vence em {} dias</span>',
                dias
            )
        else:
            return format_html(
                '<span style="color: green;">Vence em {} dias</span>',
                dias
            )
    dias_vencimento_display.short_description = 'Vencimento'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('cliente', 'ordem_producao')


class PagamentoRecebidoInline(admin.TabularInline):
    model = PagamentoRecebido
    extra = 1
    fields = ['valor_pago', 'data_pagamento', 'forma_pagamento', 'numero_documento']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('conta_receber')


@admin.register(PagamentoRecebido)
class PagamentoRecebidoAdmin(admin.ModelAdmin):
    list_display = [
        'conta_receber', 'valor_pago', 'data_pagamento', 
        'forma_pagamento', 'usuario_registro'
    ]
    list_filter = ['forma_pagamento', 'data_pagamento', 'empresa']
    search_fields = ['conta_receber__numero_conta', 'numero_documento']
    date_hierarchy = 'data_pagamento'
    
    fieldsets = (
        ('Informações do Pagamento', {
            'fields': ('conta_receber', 'valor_pago', 'data_pagamento', 'forma_pagamento')
        }),
        ('Dados Bancários', {
            'fields': ('banco', 'agencia', 'conta', 'numero_documento'),
            'classes': ('collapse',)
        }),
        ('Observações', {
            'fields': ('observacoes', 'usuario_registro'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Novo registro
            obj.usuario_registro = request.user
        super().save_model(request, obj, form, change)


@admin.register(FaturamentoMensal)
class FaturamentoMensalAdmin(admin.ModelAdmin):
    list_display = [
        'periodo_formatado', 'entradas', 'saidas', 'a_produzir',
        'valor_entradas_display', 'valor_recebido_display', 'falta_receber_display'
    ]
    list_filter = ['ano', 'mes', 'empresa']
    readonly_fields = ['data_atualizacao']
    ordering = ['-ano', '-mes']
    
    fieldsets = (
        ('Período', {
            'fields': ('mes', 'ano')
        }),
        ('Quantidades', {
            'fields': ('entradas', 'saidas', 'a_produzir')
        }),
        ('Valores Financeiros', {
            'fields': ('valor_entradas', 'valor_saidas', 'valor_recebido', 'falta_receber')
        }),
        ('Controle', {
            'fields': ('data_atualizacao',),
            'classes': ('collapse',)
        })
    )
    
    def valor_entradas_display(self, obj):
        return format_html('R$ {:.2f}', obj.valor_entradas)
    valor_entradas_display.short_description = 'Valor Entradas'
    
    def valor_recebido_display(self, obj):
        return format_html(
            '<span style="color: green; font-weight: bold;">R$ {:.2f}</span>',
            obj.valor_recebido
        )
    valor_recebido_display.short_description = 'Valor Recebido'
    
    def falta_receber_display(self, obj):
        if obj.falta_receber > 0:
            return format_html(
                '<span style="color: red; font-weight: bold;">R$ {:.2f}</span>',
                obj.falta_receber
            )
        return format_html('<span style="color: green;">R$ 0,00</span>')
    falta_receber_display.short_description = 'Falta Receber'
    
    actions = ['atualizar_faturamento_action']
    
    def atualizar_faturamento_action(self, request, queryset):
        """Action para atualizar faturamento selecionado"""
        for faturamento in queryset:
            FaturamentoMensal.atualizar_faturamento(
                faturamento.empresa, 
                faturamento.mes, 
                faturamento.ano
            )
        self.message_user(request, f'{queryset.count()} faturamentos atualizados.')
    atualizar_faturamento_action.short_description = 'Atualizar faturamentos selecionados'


# Configurar o admin para exibir apenas dados da empresa do usuário
class FinanceiroAdminMixin:
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if hasattr(request, 'empresa_atual') and request.empresa_atual:
            return qs.filter(empresa=request.empresa_atual)
        return qs.none()
    
    def save_model(self, request, obj, form, change):
        if not change and hasattr(request, 'empresa_atual'):
            obj.empresa = request.empresa_atual
        super().save_model(request, obj, form, change)


# Aplicar o mixin aos admins
ContaReceberAdmin.__bases__ = (FinanceiroAdminMixin,) + ContaReceberAdmin.__bases__
PagamentoRecebidoAdmin.__bases__ = (FinanceiroAdminMixin,) + PagamentoRecebidoAdmin.__bases__
FaturamentoMensalAdmin.__bases__ = (FinanceiroAdminMixin,) + FaturamentoMensalAdmin.__bases__
