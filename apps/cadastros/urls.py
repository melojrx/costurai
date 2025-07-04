from django.urls import path
from . import views

app_name = 'cadastros'

urlpatterns = [
    # Clientes
    path('clientes/', views.clientes_listar, name='clientes_listar'),
    path('clientes/novo/', views.cliente_criar, name='cliente_criar'),
    path('clientes/<int:pk>/', views.cliente_detalhes, name='cliente_detalhes'),
    path('clientes/<int:pk>/editar/', views.cliente_editar, name='cliente_editar'),
    path('clientes/<int:pk>/deletar/', views.cliente_deletar, name='cliente_deletar'),
    
    # Produtos
    path('produtos/', views.produtos_listar, name='produtos_listar'),
    path('produtos/novo/', views.produto_criar, name='produto_criar'),
    path('produtos/<int:pk>/', views.produto_detalhes, name='produto_detalhes'),
    path('produtos/<int:pk>/editar/', views.produto_editar, name='produto_editar'),
    path('produtos/<int:pk>/deletar/', views.produto_deletar, name='produto_deletar'),
    
    # Fornecedores
    path('fornecedores/', views.fornecedores_listar, name='fornecedores_listar'),
    path('fornecedores/novo/', views.fornecedor_criar, name='fornecedor_criar'),
    path('fornecedores/<int:pk>/', views.fornecedor_detalhes, name='fornecedor_detalhes'),
    path('fornecedores/<int:pk>/editar/', views.fornecedor_editar, name='fornecedor_editar'),
    path('fornecedores/<int:pk>/deletar/', views.fornecedor_deletar, name='fornecedor_deletar'),
    
    # APIs para busca
    path('api/clientes/buscar/', views.buscar_clientes, name='api_clientes_buscar'),
    path('api/produtos/buscar/', views.buscar_produtos, name='api_produtos_buscar'),
    
    # APIs para tamanhos
    path('api/tamanhos/', views.api_tamanhos_listar, name='api_tamanhos_listar'),
    path('api/produtos/<int:produto_id>/tamanhos/', views.api_produto_tamanhos, name='api_produto_tamanhos'),
    path('api/tamanhos/criar/', views.api_tamanho_criar, name='api_tamanho_criar'),
    
    # APIs para produtos
    path('api/produtos/<int:produto_id>/pode-excluir/', views.api_produto_pode_excluir, name='api_produto_pode_excluir'),
    path('api/produtos/<int:produto_id>/desativar/', views.api_produto_desativar, name='api_produto_desativar'),
] 