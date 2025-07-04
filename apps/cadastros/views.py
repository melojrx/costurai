from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

from apps.core.middleware import require_empresa, get_current_empresa
from .models import Cliente, Produto, ProdutoMateriaPrima, ProdutoTamanho, TamanhoProduto, Fornecedor, CategoriaProduto
from .forms import ClienteForm, ProdutoForm, FornecedorForm


# === VIEWS DE CLIENTES ===
@login_required
@require_empresa
def clientes_listar(request):
    """Lista todos os clientes da empresa"""
    empresa = get_current_empresa()
    clientes = Cliente.objects.filter(empresa=empresa)
    
    # Filtros
    search = request.GET.get('search')
    if search:
        clientes = clientes.filter(
            Q(nome__icontains=search) |
            Q(nome_fantasia__icontains=search) |
            Q(cnpj__icontains=search) |
            Q(email__icontains=search)
        )
    
    # Paginação
    paginator = Paginator(clientes, 25)
    page = request.GET.get('page')
    clientes = paginator.get_page(page)
    
    context = {
        'clientes': clientes,
        'search': search,
        'total_clientes': Cliente.objects.filter(empresa=empresa).count(),
        'clientes_ativos': Cliente.objects.filter(empresa=empresa, ativo=True).count(),
    }
    
    return render(request, 'cadastros/clientes/listar.html', context)


@login_required
@require_empresa
def cliente_criar(request):
    """Cria um novo cliente"""
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save(commit=False)
            cliente.empresa = get_current_empresa()
            cliente.save()
            messages.success(request, 'Cliente criado com sucesso!')
            return redirect('cadastros:cliente_detalhes', pk=cliente.pk)
    else:
        form = ClienteForm()
    
    return render(request, 'cadastros/clientes/form.html', {'form': form, 'title': 'Novo Cliente'})


@login_required
@require_empresa
def cliente_editar(request, pk):
    """Edita um cliente existente"""
    cliente = get_object_or_404(Cliente, pk=pk, empresa=get_current_empresa())
    
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente atualizado com sucesso!')
            return redirect('cadastros:cliente_detalhes', pk=cliente.pk)
    else:
        form = ClienteForm(instance=cliente)
    
    return render(request, 'cadastros/clientes/form.html', {
        'form': form, 
        'cliente': cliente,
        'title': f'Editar Cliente - {cliente.nome}'
    })


@login_required
@require_empresa
def cliente_detalhes(request, pk):
    """Mostra detalhes de um cliente"""
    cliente = get_object_or_404(Cliente, pk=pk, empresa=get_current_empresa())
    
    context = {
        'cliente': cliente,
    }
    
    return render(request, 'cadastros/clientes/detalhes.html', context)


@login_required
@require_empresa
def cliente_deletar(request, pk):
    """Deleta um cliente"""
    cliente = get_object_or_404(Cliente, pk=pk, empresa=get_current_empresa())
    
    if request.method == 'POST':
        nome = cliente.nome
        cliente.delete()
        messages.success(request, f'Cliente "{nome}" deletado com sucesso!')
        return redirect('cadastros:clientes_listar')
    
    return render(request, 'cadastros/clientes/confirmar_exclusao.html', {'cliente': cliente})


# === VIEWS DE PRODUTOS ===
@login_required
@require_empresa
def produtos_listar(request):
    """Lista todos os produtos da empresa"""
    empresa = get_current_empresa()
    produtos = Produto.objects.filter(empresa=empresa)
    
    # Filtros
    search = request.GET.get('search')
    if search:
        produtos = produtos.filter(
            Q(codigo__icontains=search) |
            Q(referencia__icontains=search) |
            Q(descricao__icontains=search) |
            Q(cor__icontains=search)
        )
    
    categoria = request.GET.get('categoria')
    if categoria:
        produtos = produtos.filter(produto=categoria)
    
    # Paginação
    paginator = Paginator(produtos, 25)
    page = request.GET.get('page')
    produtos = paginator.get_page(page)
    
    context = {
        'produtos': produtos,
        'search': search,
        'categoria': categoria,
        'categorias': Produto.TIPO_PRODUTO_CHOICES,
        'total_produtos': Produto.objects.filter(empresa=empresa).count(),
        'produtos_ativos': Produto.objects.filter(empresa=empresa, ativo=True).count(),
    }
    
    return render(request, 'cadastros/produtos/listar.html', context)


@login_required
@require_empresa
def produto_criar(request):
    """Cria um novo produto"""
    if request.method == 'POST':
        form = ProdutoForm(request.POST, request.FILES)
        if form.is_valid():
            produto = form.save(commit=False)
            produto.empresa = get_current_empresa()
            produto.save()
            
            messages.success(request, 'Produto criado com sucesso!')
            return redirect('cadastros:produto_detalhes', pk=produto.pk)
    else:
        form = ProdutoForm()
    
    return render(request, 'cadastros/produtos/form.html', {'form': form, 'title': 'Novo Produto'})


@login_required
@require_empresa
def produto_editar(request, pk):
    """Edita um produto existente"""
    produto = get_object_or_404(Produto, pk=pk, empresa=get_current_empresa())
    
    if request.method == 'POST':
        form = ProdutoForm(request.POST, request.FILES, instance=produto)
        if form.is_valid():
            form.save()
            
            messages.success(request, 'Produto atualizado com sucesso!')
            return redirect('cadastros:produto_detalhes', pk=produto.pk)
    else:
        form = ProdutoForm(instance=produto)
    
    return render(request, 'cadastros/produtos/form.html', {
        'form': form, 
        'produto': produto,
        'title': f'Editar Produto - {produto.codigo}'
    })


@login_required
@require_empresa
def produto_detalhes(request, pk):
    """Mostra detalhes de um produto"""
    produto = get_object_or_404(Produto, pk=pk, empresa=get_current_empresa())
    
    context = {
        'produto': produto,
        'materias_primas': produto.materias_primas.all(),
        'tamanhos': produto.tamanhos.all().order_by('ordem'),
    }
    
    return render(request, 'cadastros/produtos/detalhes.html', context)


@login_required
@require_empresa
def produto_deletar(request, pk):
    """Deleta um produto"""
    produto = get_object_or_404(Produto, pk=pk, empresa=get_current_empresa())
    
    if request.method == 'POST':
        try:
            nome = produto.nome
            produto.delete()
            messages.success(request, f'Produto "{nome}" deletado com sucesso!')
            return redirect('cadastros:produtos_listar')
        except Exception as e:
            # Verificar se é erro de proteção (produto sendo usado)
            if 'protected foreign keys' in str(e) or 'ProtectedError' in str(e):
                messages.error(request, 
                    f'Não é possível excluir o produto "{produto.nome}" pois ele está sendo usado em ordens de produção. '
                    f'Para removê-lo do sistema, você pode desativá-lo ao invés de excluí-lo.')
            else:
                messages.error(request, f'Erro ao deletar produto: {str(e)}')
            return redirect('cadastros:produtos_listar')
    
    return render(request, 'cadastros/produtos/confirmar_exclusao.html', {'produto': produto})


# === VIEWS DE FORNECEDORES ===
@login_required
@require_empresa
def fornecedores_listar(request):
    """Lista todos os fornecedores da empresa"""
    empresa = get_current_empresa()
    fornecedores = Fornecedor.objects.filter(empresa=empresa)
    
    # Filtros
    search = request.GET.get('search')
    if search:
        fornecedores = fornecedores.filter(
            Q(razao_social__icontains=search) |
            Q(nome_fantasia__icontains=search) |
            Q(cnpj_cpf__icontains=search)
        )
    
    tipo = request.GET.get('tipo')
    if tipo:
        fornecedores = fornecedores.filter(tipo_fornecedor=tipo)
    
    status_filter = request.GET.get('status')
    if status_filter == 'ativo':
        fornecedores = fornecedores.filter(ativo=True)
    elif status_filter == 'inativo':
        fornecedores = fornecedores.filter(ativo=False)
    
    # Paginação
    paginator = Paginator(fornecedores, 25)
    page = request.GET.get('page')
    fornecedores = paginator.get_page(page)
    
    # Estatísticas
    total_fornecedores = Fornecedor.objects.filter(empresa=empresa).count()
    fornecedores_ativos = Fornecedor.objects.filter(empresa=empresa, ativo=True).count()
    tipos_diferentes = Fornecedor.objects.filter(empresa=empresa).values('tipo_fornecedor').distinct().count()
    
    context = {
        'fornecedores': fornecedores,
        'search': search,
        'tipo': tipo,
        'status_filter': status_filter,
        'tipos': Fornecedor.TIPO_CHOICES,
        'total_fornecedores': total_fornecedores,
        'fornecedores_ativos': fornecedores_ativos,
        'tipos_fornecedores': tipos_diferentes,
        'is_paginated': paginator.num_pages > 1,
        'page_obj': fornecedores,
    }
    
    return render(request, 'cadastros/fornecedores/listar.html', context)


@login_required
@require_empresa
def fornecedor_criar(request):
    """Cria um novo fornecedor"""
    if request.method == 'POST':
        form = FornecedorForm(request.POST)
        if form.is_valid():
            fornecedor = form.save(commit=False)
            fornecedor.empresa = get_current_empresa()
            fornecedor.save()
            messages.success(request, 'Fornecedor criado com sucesso!')
            return redirect('cadastros:fornecedor_detalhes', pk=fornecedor.pk)
    else:
        form = FornecedorForm()
    
    return render(request, 'cadastros/fornecedores/form.html', {'form': form, 'title': 'Novo Fornecedor'})


@login_required
@require_empresa
def fornecedor_editar(request, pk):
    """Edita um fornecedor existente"""
    fornecedor = get_object_or_404(Fornecedor, pk=pk, empresa=get_current_empresa())
    
    if request.method == 'POST':
        form = FornecedorForm(request.POST, instance=fornecedor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fornecedor atualizado com sucesso!')
            return redirect('cadastros:fornecedor_detalhes', pk=fornecedor.pk)
    else:
        form = FornecedorForm(instance=fornecedor)
    
    return render(request, 'cadastros/fornecedores/form.html', {
        'form': form, 
        'fornecedor': fornecedor,
        'title': f'Editar Fornecedor - {fornecedor.razao_social}'
    })


@login_required
@require_empresa
def fornecedor_detalhes(request, pk):
    """Mostra detalhes de um fornecedor"""
    fornecedor = get_object_or_404(Fornecedor, pk=pk, empresa=get_current_empresa())
    
    context = {
        'fornecedor': fornecedor,
    }
    
    return render(request, 'cadastros/fornecedores/detalhes.html', context)


@login_required
@require_empresa
def fornecedor_deletar(request, pk):
    """Deleta um fornecedor"""
    fornecedor = get_object_or_404(Fornecedor, pk=pk, empresa=get_current_empresa())
    
    if request.method == 'POST':
        nome = fornecedor.razao_social
        fornecedor.delete()
        messages.success(request, f'Fornecedor "{nome}" deletado com sucesso!')
        return redirect('cadastros:fornecedores_listar')
    
    return render(request, 'cadastros/fornecedores/confirmar_exclusao.html', {'fornecedor': fornecedor})


# === APIs PARA BUSCA ===
@login_required
@require_empresa
def buscar_clientes(request):
    """API para buscar clientes"""
    empresa = get_current_empresa()
    term = request.GET.get('term', '')
    
    clientes = Cliente.objects.filter(
        empresa=empresa,
        ativo=True
    )
    
    if term:
        clientes = clientes.filter(
            Q(nome__icontains=term) |
            Q(cnpj__icontains=term)
        )
    
    clientes = clientes.order_by('nome')[:10]
    
    data = []
    for cliente in clientes:
        data.append({
            'id': cliente.id,
            'text': f"{cliente.nome} - {cliente.cnpj or 'Sem CNPJ'}",
            'nome': cliente.nome,
            'cnpj': cliente.cnpj,
        })
    
    return JsonResponse({'results': data})


@login_required
@require_empresa
def buscar_produtos(request):
    """API para buscar produtos"""
    empresa = get_current_empresa()
    term = request.GET.get('term', '')
    
    produtos = Produto.objects.filter(
        empresa=empresa,
        ativo=True
    )
    
    if term:
        produtos = produtos.filter(
            Q(codigo__icontains=term) |
            Q(referencia__icontains=term) |
            Q(descricao__icontains=term)
        )
    
    produtos = produtos.order_by('codigo')[:10]
    
    data = []
    for produto in produtos:
        data.append({
            'id': produto.id,
            'text': f"{produto.codigo} - {produto.referencia}",
            'codigo': produto.codigo,
            'referencia': produto.referencia,
        })
    
    return JsonResponse({'results': data})


# === APIs PARA TAMANHOS ===
@login_required
@require_empresa
def api_tamanhos_listar(request):
    """API para listar tamanhos disponíveis"""
    empresa = get_current_empresa()
    tamanhos = TamanhoProduto.objects.filter(
        empresa=empresa,
        ativo=True
    ).order_by('tipo', 'ordem', 'codigo')
    
    data = []
    for tamanho in tamanhos:
        data.append({
            'id': tamanho.id,
            'codigo': tamanho.codigo,
            'descricao': tamanho.descricao,
            'tipo': tamanho.tipo,
            'ordem': tamanho.ordem
        })
    
    return JsonResponse(data, safe=False)


@login_required
@require_empresa
def api_produto_tamanhos(request, produto_id):
    """API para listar tamanhos de um produto específico"""
    empresa = get_current_empresa()
    produto = get_object_or_404(Produto, id=produto_id, empresa=empresa)
    
    produto_tamanhos = ProdutoTamanho.objects.filter(
        produto=produto,
        ativo=True
    ).select_related('tamanho')
    
    data = []
    for pt in produto_tamanhos:
        data.append({
            'id': pt.id,
            'tamanho_id': pt.tamanho.id,
            'codigo': pt.tamanho.codigo,
            'descricao': pt.tamanho.descricao,
            'tipo': pt.tamanho.tipo,
            'preco_custo_especifico': float(pt.preco_custo_especifico) if pt.preco_custo_especifico else None,
            'preco_venda_especifico': float(pt.preco_venda_especifico) if pt.preco_venda_especifico else None,
            'preco_custo_final': float(pt.preco_custo_final) if pt.preco_custo_final else None,
            'preco_venda_final': float(pt.preco_venda_final) if pt.preco_venda_final else None,
        })
    
    return JsonResponse(data, safe=False)


@login_required
@require_empresa
@csrf_exempt
@require_http_methods(["POST"])
def api_tamanho_criar(request):
    """API para criar um novo tamanho"""
    try:
        data = json.loads(request.body)
        empresa = get_current_empresa()
        
        tamanho = TamanhoProduto.objects.create(
            empresa=empresa,
            codigo=data['codigo'],
            descricao=data['descricao'],
            tipo=data['tipo'],
            ordem=data.get('ordem', 1)
        )
        
        return JsonResponse({
            'success': True,
            'tamanho': {
                'id': tamanho.id,
                'codigo': tamanho.codigo,
                'descricao': tamanho.descricao,
                'tipo': tamanho.tipo,
                'ordem': tamanho.ordem
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@login_required
@require_empresa
def api_produto_pode_excluir(request, produto_id):
    """API para verificar se um produto pode ser excluído"""
    try:
        empresa = get_current_empresa()
        produto = get_object_or_404(Produto, id=produto_id, empresa=empresa)
        
        # Verificar se produto tem ordens de produção
        from apps.producao.models import OrdemProducao
        ops_count = OrdemProducao.objects.filter(produto=produto).count()
        
        pode_excluir = ops_count == 0
        
        return JsonResponse({
            'pode_excluir': pode_excluir,
            'motivo': 'Produto está sendo usado em ordens de produção' if not pode_excluir else '',
            'ops_count': ops_count,
            'produto_ativo': produto.ativo
        })
        
    except Exception as e:
        return JsonResponse({
            'pode_excluir': False,
            'motivo': 'Erro ao verificar produto',
            'ops_count': 0,
            'produto_ativo': True
        })


@login_required
@require_empresa
def api_produto_desativar(request, produto_id):
    """API para desativar um produto ao invés de excluir"""
    if request.method == 'POST':
        try:
            empresa = get_current_empresa()
            produto = get_object_or_404(Produto, id=produto_id, empresa=empresa)
            
            produto.ativo = False
            produto.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Produto "{produto.nome}" desativado com sucesso!'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    return JsonResponse({'success': False, 'error': 'Método não permitido'}, status=405)
