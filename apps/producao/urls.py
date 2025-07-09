from django.urls import path
from . import views

app_name = 'producao'

urlpatterns = [
    # Dashboard
    path('', views.dashboard_producao, name='dashboard'),
    path('dashboard/', views.dashboard_producao, name='dashboard_producao'),
    
    # Ordem de Produção (CRUD simplificado)
    path('ops/', views.OrdemProducaoListView.as_view(), name='ops_listar'),
    path('ops/novo/', views.OrdemProducaoCreateView.as_view(), name='op_novo'),
    path('ops/<int:pk>/', views.OrdemProducaoDetailView.as_view(), name='op_detalhes'),
    path('ops/<int:pk>/editar/', views.OrdemProducaoUpdateView.as_view(), name='op_editar'),
    
    # As URLs antigas, de API e de controle de etapas foram removidas
    # durante a simplificação do app. Elas serão recriadas conforme
    # a necessidade sobre a nova arquitetura.
] 