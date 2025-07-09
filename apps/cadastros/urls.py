from django.urls import path
from . import views

app_name = 'cadastros'

urlpatterns = [
    # Rotas para Clientes
    path('clientes/', views.clientes_listar, name='clientes_listar'),
    path('clientes/novo/', views.cliente_criar, name='cliente_novo'),
    path('clientes/<int:pk>/editar/', views.cliente_editar, name='cliente_editar'),
    path('clientes/<int:pk>/excluir/', views.cliente_deletar, name='cliente_excluir'),
    path('clientes/<int:pk>/', views.cliente_detalhes, name='cliente_detalhes'),

    # Rotas para Fornecedores
    path('fornecedores/', views.fornecedores_listar, name='fornecedores_listar'),
    path('fornecedores/novo/', views.fornecedor_criar, name='fornecedor_novo'),
    path('fornecedores/<int:pk>/editar/', views.fornecedor_editar, name='fornecedor_editar'),
    path('fornecedores/<int:pk>/excluir/', views.fornecedor_deletar, name='fornecedor_excluir'),
    path('fornecedores/<int:pk>/', views.fornecedor_detalhes, name='fornecedor_detalhes'),

    # Rotas para Produtos (usando as novas Class-Based Views)
    path('produtos/', views.ProdutoListView.as_view(), name='produtos_listar'),
    path('produtos/novo/', views.ProdutoCreateView.as_view(), name='produto_novo'),
    path('produtos/<int:pk>/', views.ProdutoDetailView.as_view(), name='produto_detalhes'),
    path('produtos/<int:pk>/editar/', views.ProdutoUpdateView.as_view(), name='produto_editar'),
    path('produtos/<int:pk>/excluir/', views.ProdutoDeleteView.as_view(), name='produto_excluir'),

    # Rotas AJAX
    # path('ajax/buscar-cep/', views.buscar_cep, name='buscar_cep'),
] 