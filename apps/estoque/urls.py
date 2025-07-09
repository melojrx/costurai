from django.urls import path, include
from . import views

app_name = 'estoque'

urlpatterns = [
    # === DASHBOARD ===
    path('', views.EstoqueDashboardView.as_view(), name='dashboard'),
    
    # === MATÉRIAS-PRIMAS ===
    path('materias-primas/', views.MateriaPrimaListView.as_view(), name='materia_prima_list'),
    path('materias-primas/nova/', views.MateriaPrimaCreateView.as_view(), name='materia_prima_create'),
    path('materias-primas/<int:pk>/', views.MateriaPrimaDetailView.as_view(), name='materia_prima_detail'),
    path('materias-primas/<int:pk>/editar/', views.MateriaPrimaUpdateView.as_view(), name='materia_prima_update'),
    path('materias-primas/<int:pk>/excluir/', views.MateriaPrimaDeleteView.as_view(), name='materia_prima_delete'),
    
    # === CATEGORIAS ===
    path('categorias/', views.CategoriaMateriaPrimaListView.as_view(), name='categoria_list'),
    path('categorias/nova/', views.CategoriaMateriaPrimaCreateView.as_view(), name='categoria_create'),
    path('categorias/<int:pk>/editar/', views.CategoriaMateriaPrimaUpdateView.as_view(), name='categoria_update'),
    path('categorias/<int:pk>/excluir/', views.CategoriaMateriaPrimaDeleteView.as_view(), name='categoria_delete'),
    
    # === MOVIMENTAÇÕES ===
    path('movimentacoes/', views.MovimentacaoEstoqueListView.as_view(), name='movimentacao_list'),
    path('movimentacoes/entrada/', views.EntradaEstoqueCreateView.as_view(), name='entrada_create'),
    path('movimentacoes/saida/', views.SaidaEstoqueCreateView.as_view(), name='saida_create'),
    path('movimentacoes/ajuste/', views.AjusteEstoqueCreateView.as_view(), name='ajuste_create'),
    path('movimentacoes/<int:pk>/', views.MovimentacaoEstoqueDetailView.as_view(), name='movimentacao_detail'),
    path('movimentacoes/<int:pk>/cancelar/', views.CancelarMovimentacaoView.as_view(), name='movimentacao_cancelar'),
    
    # === INVENTÁRIO ===
    path('inventarios/', views.InventarioFisicoListView.as_view(), name='inventario_list'),
    path('inventarios/novo/', views.InventarioFisicoCreateView.as_view(), name='inventario_create'),
    path('inventarios/<int:pk>/', views.InventarioFisicoDetailView.as_view(), name='inventario_detail'),
    path('inventarios/<int:pk>/iniciar/', views.IniciarInventarioView.as_view(), name='inventario_iniciar'),
    path('inventarios/<int:pk>/finalizar/', views.FinalizarInventarioView.as_view(), name='inventario_finalizar'),
    path('inventarios/<int:pk>/cancelar/', views.CancelarInventarioView.as_view(), name='inventario_cancelar'),
    path('inventarios/<int:pk>/item/<int:item_pk>/contar/', views.ContarItemInventarioView.as_view(), name='inventario_contar_item'),
    
    # === LOTES ===
    path('lotes/', views.LoteMateriaPrimaListView.as_view(), name='lote_list'),
    path('lotes/novo/', views.LoteMateriaPrimaCreateView.as_view(), name='lote_create'),
    path('lotes/<int:pk>/', views.LoteMateriaPrimaDetailView.as_view(), name='lote_detail'),
    path('lotes/<int:pk>/bloquear/', views.BloquearLoteView.as_view(), name='lote_bloquear'),
    path('lotes/<int:pk>/desbloquear/', views.DesbloquearLoteView.as_view(), name='lote_desbloquear'),
    
    # === RELATÓRIOS ===
    path('relatorios/', views.RelatoriosEstoqueView.as_view(), name='relatorios'),
    path('relatorios/estoque-atual/', views.RelatorioEstoqueAtualView.as_view(), name='relatorio_estoque_atual'),
    path('relatorios/movimentacoes/', views.RelatorioMovimentacoesView.as_view(), name='relatorio_movimentacoes'),
    path('relatorios/custos/', views.RelatorioCustosView.as_view(), name='relatorio_custos'),
    path('relatorios/lotes-vencimento/', views.RelatorioLotesVencimentoView.as_view(), name='relatorio_lotes_vencimento'),
    
    # === UTILIDADES ===
    path('gerar-codigo-materia-prima/', views.materia_prima.gerar_codigo_materia_prima, name='gerar_codigo_materia_prima'),
    
    # === APIs ===
    path('api/', include([
        path('materias-primas/', views.api.listar_materias_primas_json, name='api_materias_primas'),
        path('materias-primas/<int:pk>/estoque/', views.api.verificar_estoque_json, name='api_verificar_estoque'),
        path('materia-prima/<int:pk>/', views.api.materia_prima_detail_json, name='api_materia_prima_detail'),
        path('dashboard-data/', views.api.dashboard_data_json, name='api_dashboard_data'),
        path('alertas/', views.api.alertas_estoque_json, name='api_alertas'),
        path('lotes/<int:materia_prima_id>/', views.api.listar_lotes_json, name='api_lotes'),
        path('inventario/resumo/', views.ResumoInventarioAPIView.as_view(), name='api_resumo_inventario'),
    ])),
] 