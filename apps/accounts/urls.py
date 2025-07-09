from django.urls import path, include
from . import views

app_name = 'accounts'

urlpatterns = [
    # Autenticação customizada (deve vir ANTES das URLs padrão)
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('registro/', views.registro_view, name='registro'),  # Redirect para escolha
    
    # Cadastro em etapas
    path('cadastro/', views.registro_escolha_view, name='registro_escolha'),
    path('cadastro/etapa1/', views.registro_etapa1_view, name='registro_etapa1'),
    path('cadastro/etapa2/', views.registro_etapa2_view, name='registro_etapa2'),
    path('cadastro/etapa3/', views.registro_etapa3_view, name='registro_etapa3'),
    
    # Perfil do usuário
    path('perfil/', views.perfil_view, name='perfil'),
    
    # Gestão de conta
    path('conta/', views.gestao_conta_view, name='gestao_conta'),
    
    # AJAX endpoints
    path('ajax/atualizar-perfil/', views.atualizar_perfil_ajax, name='atualizar_perfil_ajax'),
    path('ajax/atualizar-empresa/', views.atualizar_empresa_ajax, name='atualizar_empresa_ajax'),
    path('ajax/alterar-senha/', views.alterar_senha_ajax, name='alterar_senha_ajax'),
    path('ajax/upgrade-plano/', views.upgrade_plano_view, name='upgrade_plano'),
    path('ajax/validar-cupom/', views.validar_cupom_ajax, name='validar_cupom'),
    path('ajax/estender-trial/', views.estender_trial_view, name='estender_trial'),
    path('ajax/aplicar-cupom-trial/', views.aplicar_cupom_trial_view, name='aplicar_cupom_trial'),
    path('ajax/historico-assinatura/', views.historico_assinatura_view, name='historico_assinatura'),
    
    # Convites (para implementar futuramente)
    # path('convite/<str:token>/', views.aceitar_convite_view, name='aceitar_convite'),
    
    # URLs de autenticação padrão do Django (devem vir POR ÚLTIMO para não sobrescrever as customizadas)
    path('', include('django.contrib.auth.urls')),
] 