from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import (
    Empresa, PlanoAssinatura, AssinaturaEmpresa, 
    UsuarioEmpresa, AuditLog, CupomDesconto,
    TransacaoPagamento, HistoricoAssinatura, ConfiguracaoBilling
)


@admin.register(PlanoAssinatura)
class PlanoAssinaturaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'tipo', 'preco_mensal', 'max_empresas', 'max_ops_mes', 'ativo', 'destaque']
    list_filter = ['tipo', 'ativo', 'destaque', 'visivel_site']
    search_fields = ['nome', 'descricao']
    ordering = ['ordem_exibicao', 'preco_mensal']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'tipo', 'descricao', 'descricao_curta')
        }),
        ('Preços', {
            'fields': ('preco_mensal', 'preco_anual', 'desconto_anual')
        }),
        ('Limitações', {
            'fields': ('max_empresas', 'max_ops_mes', 'max_usuarios', 'max_storage_gb')
        }),
        ('Features', {
            'fields': ('tem_api', 'tem_relatorios_avancados', 'tem_suporte_prioritario', 
                      'tem_backup_automatico', 'tem_integracao_contabil', 'tem_multiempresa')
        }),
        ('Trial e Billing', {
            'fields': ('dias_trial', 'permite_trial', 'permite_upgrade', 'permite_downgrade', 'requer_cartao_trial')
        }),
        ('Exibição', {
            'fields': ('destaque', 'ordem_exibicao', 'cor_tema', 'ativo', 'visivel_site')
        })
    )


@admin.register(CupomDesconto)
class CupomDescontoAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'descricao_resumida', 'tipo_desconto', 'valor_desconto', 
                   'status_cupom', 'vezes_usado', 'limite_uso', 'data_fim']
    list_filter = ['tipo_desconto', 'ativo', 'apenas_novos_clientes', 'data_inicio', 'data_fim']
    search_fields = ['codigo', 'descricao']
    ordering = ['-created_at']
    filter_horizontal = ['planos_aplicaveis']
    
    fieldsets = (
        ('Informações do Cupom', {
            'fields': ('codigo', 'descricao')
        }),
        ('Configuração do Desconto', {
            'fields': ('tipo_desconto', 'valor_desconto')
        }),
        ('Período de Validade', {
            'fields': ('data_inicio', 'data_fim')
        }),
        ('Limitações de Uso', {
            'fields': ('limite_uso', 'vezes_usado', 'apenas_novos_clientes')
        }),
        ('Aplicabilidade', {
            'fields': ('planos_aplicaveis',)
        }),
        ('Status', {
            'fields': ('ativo',)
        })
    )
    
    readonly_fields = ['vezes_usado']
    
    def descricao_resumida(self, obj):
        return obj.descricao[:50] + "..." if len(obj.descricao) > 50 else obj.descricao
    descricao_resumida.short_description = 'Descrição'
    
    def status_cupom(self, obj):
        if not obj.ativo:
            return format_html('<span style="color: red;">Inativo</span>')
        elif not obj.esta_valido:
            return format_html('<span style="color: orange;">Expirado</span>')
        elif obj.limite_uso and obj.vezes_usado >= obj.limite_uso:
            return format_html('<span style="color: orange;">Limite Atingido</span>')
        else:
            return format_html('<span style="color: green;">Válido</span>')
    status_cupom.short_description = 'Status'
    
    actions = ['ativar_cupons', 'desativar_cupons', 'resetar_uso']
    
    def ativar_cupons(self, request, queryset):
        count = queryset.update(ativo=True)
        self.message_user(request, f'{count} cupons foram ativados.')
    ativar_cupons.short_description = "Ativar cupons selecionados"
    
    def desativar_cupons(self, request, queryset):
        count = queryset.update(ativo=False)
        self.message_user(request, f'{count} cupons foram desativados.')
    desativar_cupons.short_description = "Desativar cupons selecionados"
    
    def resetar_uso(self, request, queryset):
        count = queryset.update(vezes_usado=0)
        self.message_user(request, f'Contador de uso resetado para {count} cupons.')
    resetar_uso.short_description = "Resetar contador de uso"


@admin.register(TransacaoPagamento)
class TransacaoPagamentoAdmin(admin.ModelAdmin):
    list_display = ['id_transacao', 'empresa', 'plano', 'tipo_transacao', 
                   'valor_final', 'status', 'data_criacao']
    list_filter = ['status', 'tipo_transacao', 'gateway', 'data_criacao']
    search_fields = ['id_transacao', 'empresa__nome', 'plano__nome']
    ordering = ['-data_criacao']
    readonly_fields = ['id_transacao', 'data_criacao', 'dados_gateway']
    
    fieldsets = (
        ('Identificação', {
            'fields': ('id_transacao', 'id_gateway')
        }),
        ('Relacionamentos', {
            'fields': ('empresa', 'assinatura', 'plano', 'cupom')
        }),
        ('Dados da Transação', {
            'fields': ('tipo_transacao', 'gateway', 'status')
        }),
        ('Valores', {
            'fields': ('valor_original', 'valor_desconto', 'valor_final')
        }),
        ('Dados do Pagamento', {
            'fields': ('metodo_pagamento', 'ultimos_4_digitos')
        }),
        ('Controle Temporal', {
            'fields': ('data_criacao', 'data_processamento', 'data_aprovacao', 'data_vencimento')
        }),
        ('Dados Adicionais', {
            'fields': ('observacoes', 'ip_address', 'user_agent', 'dados_gateway'),
            'classes': ('collapse',)
        })
    )


@admin.register(HistoricoAssinatura)
class HistoricoAssinaturaAdmin(admin.ModelAdmin):
    list_display = ['assinatura', 'acao', 'plano_anterior', 'plano_novo', 
                   'valor_novo', 'usuario', 'data_mudanca']
    list_filter = ['acao', 'data_mudanca']
    search_fields = ['assinatura__empresa__nome', 'plano_novo__nome', 'usuario__username']
    ordering = ['-data_mudanca']
    readonly_fields = ['data_mudanca']


@admin.register(ConfiguracaoBilling)
class ConfiguracaoBillingAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Stripe', {
            'fields': ('stripe_public_key', 'stripe_secret_key', 'stripe_webhook_secret')
        }),
        ('Mercado Pago', {
            'fields': ('mercadopago_public_key', 'mercadopago_access_token')
        }),
        ('Configurações de Cobrança', {
            'fields': ('dias_trial_padrao', 'dias_tolerancia_pagamento', 
                      'enviar_lembrete_pagamento', 'dias_lembrete')
        }),
        ('Impostos', {
            'fields': ('percentual_imposto',)
        }),
        ('Emails', {
            'fields': ('email_cobranca', 'email_suporte')
        })
    )


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'cnpj', 'cidade', 'estado', 'ativa', 'data_cadastro']
    list_filter = ['ativa', 'estado', 'data_cadastro']
    search_fields = ['nome', 'razao_social', 'cnpj']
    ordering = ['nome']
    readonly_fields = ['data_cadastro']


@admin.register(AssinaturaEmpresa)
class AssinaturaEmpresaAdmin(admin.ModelAdmin):
    list_display = ['empresa', 'plano', 'status', 'data_inicio', 'data_proximo_pagamento', 'trial_ativo']
    list_filter = ['status', 'plano', 'trial_ativo']
    search_fields = ['empresa__nome']
    ordering = ['-data_inicio']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('empresa', 'plano', 'status')
        }),
        ('Datas', {
            'fields': ('data_inicio', 'data_fim', 'data_proximo_pagamento')
        }),
        ('Trial', {
            'fields': ('trial_ativo', 'trial_fim')
        })
    )


# UserProfile admin movido para apps.accounts.admin


@admin.register(UsuarioEmpresa)
class UsuarioEmpresaAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'empresa', 'role', 'ativo', 'data_vinculo']
    list_filter = ['role', 'ativo', 'empresa']
    search_fields = ['usuario__username', 'empresa__nome']
    ordering = ['-data_vinculo']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'usuario', 'empresa', 'acao', 'modelo', 'registro_id']
    list_filter = ['acao', 'modelo', 'timestamp']
    search_fields = ['usuario__username', 'empresa__nome']
    ordering = ['-timestamp']
    readonly_fields = ['timestamp']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False 