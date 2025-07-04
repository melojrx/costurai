from django.urls import path
from . import views

app_name = 'empresas'

urlpatterns = [
    # URLs principais
    path('selecionar/', views.selecionar_empresa, name='selecionar'),
    path('criar/', views.criar_empresa, name='criar'),
    path('dashboard/', views.dashboard_empresa, name='dashboard'),
    path('configuracoes/', views.configuracoes_empresa, name='configuracoes'),
    
    # Ajax
    path('ajax/trocar/', views.ajax_trocar_empresa, name='ajax_trocar'),
] 