from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'producao'

# Router para APIs REST
router = DefaultRouter()
router.register(r'api/ops', views.OrdemProducaoViewSet, basename='api-ops')
router.register(r'api/departamentos', views.DepartamentoViewSet, basename='api-departamentos')
router.register(r'api/materias-primas', views.MateriaPrimaViewSet, basename='api-materias-primas')
router.register(r'api/processos', views.ProcessoProducaoViewSet, basename='api-processos')

# URLs tradicionais (Django Templates)
urlpatterns = [
    # Dashboard e página principal
    path('', views.dashboard_producao, name='dashboard'),
    path('dashboard/', views.dashboard_producao, name='dashboard_producao'),
    
    # Ordens de Produção - Views tradicionais
    path('ops/', views.ops_listar, name='ops_listar'),
    path('ops/novo/', views.op_form, name='op_novo'),
    path('ops/<int:op_id>/', views.op_detalhes, name='op_detalhes'),
    path('ops/<int:op_id>/editar/', views.op_form, name='op_editar'),
    path('ops/<int:op_id>/avancar/', views.avancar_status_op, name='avancar_status_op'),
    path('ops/<int:op_id>/pdf/', views.op_pdf, name='op_pdf'),
    path('ops/<int:op_id>/materias/', views.materias_op, name='materias_op'),
    path('ops/exportar/', views.exportar_ops, name='exportar_ops'),
    
    # Matéria Prima
    path('materias-prima/', views.materias_prima_listar, name='materias_prima'),
    
    # AJAX endpoints
    path('ajax/atualizar-progresso/', views.atualizar_progresso_op, name='atualizar_progresso'),
    path('ajax/buscar-clientes/', views.buscar_clientes, name='buscar_clientes'),
    path('ajax/buscar-produtos/', views.buscar_produtos, name='buscar_produtos'),
    
    # APIs REST
    path('', include(router.urls)),
]

# URLs específicas para APIs REST (endpoints customizados)
api_urlpatterns = [
    # Estatísticas e Dashboard
    path('api/dashboard/stats/', 
         views.OrdemProducaoViewSet.as_view({'get': 'dashboard_stats'}), 
         name='api-dashboard-stats'),
    
    # Operações em lote
    path('api/ops/bulk-update-status/', 
         views.OrdemProducaoViewSet.as_view({'post': 'bulk_update_status'}), 
         name='api-bulk-update-status'),
    
    path('api/ops/bulk-update-progress/', 
         views.OrdemProducaoViewSet.as_view({'post': 'bulk_update_progress'}), 
         name='api-bulk-update-progress'),
    
    # Controle de produção
    path('api/ops/<int:pk>/iniciar-producao/', 
         views.OrdemProducaoViewSet.as_view({'post': 'iniciar_producao'}), 
         name='api-iniciar-producao'),
    
    path('api/ops/<int:pk>/concluir-producao/', 
         views.OrdemProducaoViewSet.as_view({'post': 'concluir_producao'}), 
         name='api-concluir-producao'),
    
    # Matérias primas
    path('api/materias-primas/baixo-estoque/', 
         views.MateriaPrimaViewSet.as_view({'get': 'baixo_estoque'}), 
         name='api-materias-baixo-estoque'),
    
    # Processos de produção
    path('api/processos/<int:pk>/iniciar/', 
         views.ProcessoProducaoViewSet.as_view({'post': 'iniciar_processo'}), 
         name='api-iniciar-processo'),
    
    path('api/processos/<int:pk>/concluir/', 
         views.ProcessoProducaoViewSet.as_view({'post': 'concluir_processo'}), 
         name='api-concluir-processo'),
]

# Adicionar URLs da API às principais
urlpatterns += api_urlpatterns

# Adicionar URLs que estavam fora da lista principal
urlpatterns += [
    # Linhas de Produção
    path('linhas/', views.linhas_producao, name='linhas'),
    path('linhas/<int:linha_id>/', views.linha_detalhes, name='linha_detalhes'),
    
    # Acompanhamento de Produção
    path('acompanhar/', views.acompanhar_producao, name='acompanhar_producao'),

    # Relatórios
    path('relatorios/', views.relatorios_producao, name='relatorios'),
    path('relatorios/producao/', views.relatorio_producao, name='relatorio_producao'),
    path('relatorios/eficiencia/', views.relatorio_eficiencia, name='relatorio_eficiencia'),

    # APIs AJAX - Controle de Etapas
    path('api/etapa/<int:controle_id>/iniciar/', views.api_iniciar_etapa, name='api_iniciar_etapa'),
    path('api/etapa/<int:controle_id>/concluir/', views.api_concluir_etapa, name='api_concluir_etapa'),
    path('api/etapa/<int:controle_id>/pausar/', views.api_pausar_etapa, name='api_pausar_etapa'),
    path('api/etapa/<int:controle_id>/retomar/', views.api_retomar_etapa, name='api_retomar_etapa'),
    
    # APIs AJAX - Controle de Linhas
    path('api/linha/<int:linha_id>/status/', views.api_status_linha, name='api_status_linha'),
    path('api/linha/<int:linha_id>/alterar-status/', views.api_alterar_status_linha, name='api_alterar_status_linha'),

    # APIs AJAX antigas
    path('api/op/<int:op_id>/status/', views.atualizar_status_op, name='api_status_op'),
    path('api/linha/<int:linha_id>/parar/', views.parar_linha, name='api_parar_linha'),
    path('api/buscar-produto/', views.buscar_produto, name='api_buscar_produto'),
] 