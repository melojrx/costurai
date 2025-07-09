from django.urls import path
from . import views

app_name = 'cadastros'

urlpatterns = [
    # === CLIENTES ===
    path('clientes/', views.clientes_listar, name='clientes_listar'),
    path('clientes/novo/', views.cliente_criar, name='cliente_novo'),
    path('clientes/<int:pk>/', views.cliente_detalhes, name='cliente_detalhes'),
    path('clientes/<int:pk>/editar/', views.cliente_editar, name='cliente_editar'),
    path('clientes/<int:pk>/deletar/', views.cliente_deletar, name='cliente_deletar'),
    
    # === FORNECEDORES ===
    path('fornecedores/', views.fornecedores_listar, name='fornecedores_listar'),
    path('fornecedores/novo/', views.fornecedor_criar, name='fornecedor_novo'),
    path('fornecedores/<int:pk>/', views.fornecedor_detalhes, name='fornecedor_detalhes'),
    path('fornecedores/<int:pk>/editar/', views.fornecedor_editar, name='fornecedor_editar'),
    path('fornecedores/<int:pk>/deletar/', views.fornecedor_deletar, name='fornecedor_deletar'),
    
    # === PRODUTOS ===
    path('produtos/', views.ProdutoListView.as_view(), name='produtos_listar'),
    path('produtos/novo/', views.ProdutoCreateView.as_view(), name='produto_novo'),
    path('produtos/<int:pk>/', views.ProdutoDetailView.as_view(), name='produto_detalhes'),
    path('produtos/<int:pk>/editar/', views.ProdutoUpdateView.as_view(), name='produto_editar'),
    path('produtos/<int:pk>/deletar/', views.ProdutoDeleteView.as_view(), name='produto_deletar'),
    
    # === APIs DE BUSCA ===
    path('api/clientes/', views.buscar_clientes, name='buscar_clientes'),
    path('api/produtos/', views.buscar_produtos, name='buscar_produtos'),
    path('api/tamanhos/', views.api_tamanhos_listar, name='api_tamanhos'),
    path('api/produto/<int:produto_id>/tamanhos/', views.api_produto_tamanhos, name='api_produto_tamanhos'),
    path('api/tamanho/criar/', views.api_tamanho_criar, name='api_tamanho_criar'),
    path('api/produto/<int:produto_id>/pode-excluir/', views.api_produto_pode_excluir, name='api_produto_pode_excluir'),
    path('api/produto/<int:produto_id>/desativar/', views.api_produto_desativar, name='api_produto_desativar'),
    
    # === APIs MATÉRIAS-PRIMAS ===
    path('api/materia-prima/<int:materia_prima_id>/dados/', views.api_materia_prima_dados, name='api_materia_prima_dados'),
    path('api/calcular-custo-produto/', views.api_calcular_custo_produto, name='api_calcular_custo_produto'),
    path('api/categorias-materia-prima/', views.api_categorias_materia_prima, name='api_categorias_materia_prima'),
    
    # Rotas AJAX
    path('ajax/gerar-codigo-produto/', views.gerar_codigo_produto, name='gerar_codigo_produto'),
    path('ajax/criar-categoria-produto/', views.criar_categoria_produto, name='criar_categoria_produto'),
    path('ajax/criar-ncm/', views.criar_ncm, name='criar_ncm'),
    path('ajax/buscar-valores-grade/', views.buscar_valores_grade, name='buscar_valores_grade'),
    path('ajax/criar-materia-prima-rapida/', views.criar_materia_prima_rapida, name='criar_materia_prima_rapida'),
    # path('ajax/buscar-cep/', views.buscar_cep, name='buscar_cep'),
] 