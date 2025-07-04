from django.urls import path
from . import views

app_name = 'financeiro'

urlpatterns = [
    # Relatório Financeiro (Dashboard)
    path('', views.dashboard_financeiro, name='relatorio_financeiro'),
    path('relatorio/', views.dashboard_financeiro, name='relatorio_financeiro_alt'),
    
    # Contas a Receber
    path('contas-receber/', views.contas_receber_listar, name='contas_receber'),
    path('contas-receber/nova/', views.conta_nova, name='conta_nova'),
    path('contas-receber/<int:conta_id>/', views.conta_receber_detalhes, name='conta_detalhes'),
    path('contas-receber/<int:conta_id>/pagamento/', views.registrar_pagamento, name='registrar_pagamento'),
    
    # Contas a Pagar
    path('contas-pagar/', views.contas_pagar_listar, name='contas_pagar'),
    path('contas-pagar/nova/', views.conta_pagar_nova, name='conta_pagar_nova'),
    path('contas-pagar/<int:conta_id>/', views.conta_pagar_detalhes, name='conta_pagar_detalhes'),
    path('contas-pagar/<int:conta_id>/pagamento/', views.registrar_pagamento_conta_pagar, name='registrar_pagamento_conta_pagar'),
    
    # Categorias e Subcategorias
    path('categorias/', views.categorias_listar, name='categorias_listar'),
    path('categorias/nova/', views.categoria_nova, name='categoria_nova'),
    path('categorias/<int:categoria_id>/subcategoria/nova/', views.subcategoria_nova, name='subcategoria_nova'),
    
    # Relatórios de Faturamento
    path('faturamento/', views.relatorio_faturamento, name='relatorio_faturamento'),
    path('faturamento/exportar/', views.exportar_faturamento, name='exportar_faturamento'),
    
    # Relatórios Financeiros Integrados
    path('relatorios/dre/', views.relatorio_dre, name='relatorio_dre'),
    path('relatorios/fluxo-caixa/', views.relatorio_fluxo_caixa, name='relatorio_fluxo_caixa'),
    
    # AJAX Endpoints
    path('ajax/atualizar-faturamento/', views.atualizar_faturamento_ajax, name='atualizar_faturamento'),
    path('ajax/buscar-contas/', views.buscar_contas_ajax, name='buscar_contas'),
    path('ajax/buscar-subcategorias/', views.buscar_subcategorias_ajax, name='buscar_subcategorias'),
    path('ajax/buscar-fornecedores/', views.buscar_fornecedores_ajax, name='buscar_fornecedores'),
] 