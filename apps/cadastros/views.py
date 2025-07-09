from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from django.views.generic import CreateView, UpdateView, ListView, DetailView
from django.urls import reverse_lazy
from django.db import transaction
from django.http import Http404
from django.utils.decorators import method_decorator

from apps.core.middleware import require_empresa, get_current_empresa
from .models import Cliente, Produto, ProdutoMateriaPrima, ProdutoTamanho, TamanhoProduto, Fornecedor, CategoriaProduto, NCM
from .forms import ClienteForm, FornecedorForm, ProdutoForm, ProdutoMateriaPrimaFormSet
from apps.core.mixins import TenantMixin


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
            
            # Se for requisição AJAX, retornar JSON
            if request.headers.get('X-CSRFToken'):
                return JsonResponse({
                    'id': fornecedor.id,
                    'nome': fornecedor.nome_fantasia or fornecedor.razao_social,
                    'success': True
                })
            
            messages.success(request, 'Fornecedor criado com sucesso!')
            return redirect('cadastros:fornecedor_detalhes', pk=fornecedor.pk)
        else:
            # Se for requisição AJAX, retornar erro JSON
            if request.headers.get('X-CSRFToken'):
                errors = []
                for field, error_list in form.errors.items():
                    for error in error_list:
                        errors.append(f"{field}: {error}")
                
                return JsonResponse({
                    'error': '; '.join(errors),
                    'success': False
                }, status=400)
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
            Q(descricao__icontains=term)
        )
    
    produtos = produtos.order_by('codigo')[:10]
    
    data = []
    for produto in produtos:
        data.append({
            'id': produto.id,
            'text': f"{produto.codigo} - {produto.descricao}",
            'codigo': produto.codigo,
            'descricao': produto.descricao,
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


# === CLASS-BASED VIEWS PARA PRODUTOS ===
@method_decorator([login_required, require_empresa], name='dispatch')
class ProdutoListView(TenantMixin, ListView):
    model = Produto
    template_name = 'cadastros/produtos/listar.html'
    context_object_name = 'produtos'

@method_decorator([login_required, require_empresa], name='dispatch')
class ProdutoDetailView(TenantMixin, DetailView):
    model = Produto
    template_name = 'cadastros/produtos/detalhes.html'
    context_object_name = 'produto'

@method_decorator([login_required, require_empresa], name='dispatch')
class ProdutoCreateView(TenantMixin, CreateView):
    model = Produto
    form_class = ProdutoForm
    template_name = 'cadastros/produtos/form.html'
    success_url = reverse_lazy('cadastros:produtos_listar')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['empresa'] = get_current_empresa()
        return kwargs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['materias_primas'] = ProdutoMateriaPrimaFormSet(self.request.POST)
        else:
            data['materias_primas'] = ProdutoMateriaPrimaFormSet()
        return data

    def form_valid(self, form):
        form.instance.empresa = get_current_empresa()
        context = self.get_context_data()
        materias_primas = context['materias_primas']
        with transaction.atomic():
            self.object = form.save()
            if materias_primas.is_valid():
                materias_primas.instance = self.object
                materias_primas.save()
        return super().form_valid(form)

@method_decorator([login_required, require_empresa], name='dispatch')
class ProdutoUpdateView(TenantMixin, UpdateView):
    model = Produto
    form_class = ProdutoForm
    template_name = 'cadastros/produtos/form.html'
    success_url = reverse_lazy('cadastros:produtos_listar')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['empresa'] = get_current_empresa()
        return kwargs

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['materias_primas'] = ProdutoMateriaPrimaFormSet(self.request.POST, instance=self.object)
        else:
            data['materias_primas'] = ProdutoMateriaPrimaFormSet(instance=self.object)
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        materias_primas = context['materias_primas']
        with transaction.atomic():
            self.object = form.save()
            if materias_primas.is_valid():
                materias_primas.instance = self.object
                materias_primas.save()
        return super().form_valid(form)

@method_decorator([login_required, require_empresa], name='dispatch')
class ProdutoDeleteView(TenantMixin, DetailView):
    model = Produto
    template_name = 'cadastros/produtos/confirmar_exclusao.html'
    context_object_name = 'produto'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        empresa_atual = get_current_empresa()
        if not obj.empresa == empresa_atual:
            raise Http404("Produto não encontrado ou não pertence à sua empresa.")
        return obj

    def post(self, request, *args, **kwargs):
        produto = self.get_object()
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


# === FUNÇÃO PARA GERAR CÓDIGO AUTOMÁTICO DE PRODUTOS ===
@login_required
@require_empresa
def gerar_codigo_produto(request):
    """Gera código automático para produto seguindo o padrão PR001, PR002, etc."""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Requisição inválida'}, status=400)
    
    empresa = get_current_empresa()
    
    # Buscar o último código usado
    ultimo_produto = Produto.objects.filter(
        empresa=empresa,
        codigo__startswith='PR'
    ).order_by('-codigo').first()
    
    if ultimo_produto:
        try:
            # Extrair número do último código (ex: PR001 -> 1)
            ultimo_numero = int(ultimo_produto.codigo.replace('PR', ''))
            proximo_numero = ultimo_numero + 1
        except (ValueError, TypeError):
            # Se não conseguir extrair número, começar do 1
            proximo_numero = 1
    else:
        # Primeiro produto
        proximo_numero = 1
    
    # Gerar código com 3 dígitos (PR001, PR002, etc.)
    novo_codigo = f"PR{proximo_numero:03d}"
    
    # Verificar se código já existe (segurança)
    while Produto.objects.filter(empresa=empresa, codigo=novo_codigo).exists():
        proximo_numero += 1
        novo_codigo = f"PR{proximo_numero:03d}"
    
    return JsonResponse({
        'codigo': novo_codigo,
        'numero': proximo_numero
    })


# === VIEWS AJAX PARA CATEGORIA DE PRODUTO ===
@login_required
@require_empresa
def criar_categoria_produto(request):
    """Cria nova categoria de produto via AJAX"""
    if request.method == 'POST':
        try:
            empresa = get_current_empresa()
            
            nome = request.POST.get('nome', '').strip()
            descricao = request.POST.get('descricao', '').strip()
            
            if not nome:
                return JsonResponse({
                    'success': False,
                    'error': 'Nome da categoria é obrigatório'
                }, status=400)
            
            # Verificar se categoria já existe
            if CategoriaProduto.objects.filter(empresa=empresa, nome=nome).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Já existe uma categoria com este nome'
                }, status=400)
            
            # Criar categoria
            categoria = CategoriaProduto.objects.create(
                empresa=empresa,
                nome=nome,
                descricao=descricao,
                ativo=True
            )
            
            return JsonResponse({
                'success': True,
                'id': categoria.id,
                'nome': categoria.nome
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({'success': False, 'error': 'Método não permitido'}, status=405)


# === VIEWS AJAX PARA NCM ===
@login_required
@require_empresa
def criar_ncm(request):
    """Cria novo NCM via AJAX"""
    if request.method == 'POST':
        try:
            empresa = get_current_empresa()
            
            codigo = request.POST.get('codigo', '').strip()
            descricao = request.POST.get('descricao', '').strip()
            aliquota_ipi = request.POST.get('aliquota_ipi', '0')
            
            if not codigo:
                return JsonResponse({
                    'success': False,
                    'error': 'Código NCM é obrigatório'
                }, status=400)
            
            if not descricao:
                return JsonResponse({
                    'success': False,
                    'error': 'Descrição do NCM é obrigatória'
                }, status=400)
            
            # Verificar se NCM já existe
            if NCM.objects.filter(empresa=empresa, codigo=codigo).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Já existe um NCM com este código'
                }, status=400)
            
            # Validar alíquota IPI
            try:
                aliquota_ipi = float(aliquota_ipi)
                if aliquota_ipi < 0 or aliquota_ipi > 100:
                    raise ValueError("Alíquota deve estar entre 0 e 100")
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': 'Alíquota IPI deve ser um número entre 0 e 100'
                }, status=400)
            
            # Criar NCM
            ncm = NCM.objects.create(
                empresa=empresa,
                codigo=codigo,
                descricao=descricao,
                aliquota_ipi=aliquota_ipi,
                ativo=True
            )
            
            return JsonResponse({
                'success': True,
                'id': ncm.id,
                'codigo': ncm.codigo,
                'descricao': ncm.descricao,
                'display': f"{ncm.codigo} - {ncm.descricao}"
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({'success': False, 'error': 'Método não permitido'}, status=405)


# === VIEWS AJAX PARA TIPOS DE GRADE ===
@login_required
@require_empresa
def buscar_valores_grade(request):
    """Busca valores de grade baseados no tipo selecionado"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Requisição inválida'}, status=400)
    
    from .models import TipoGrade, ValorGrade
    
    tipo_grade_id = request.GET.get('tipo_grade_id')
    
    if not tipo_grade_id:
        return JsonResponse({'error': 'ID do tipo de grade é obrigatório'}, status=400)
    
    try:
        empresa = get_current_empresa()
        tipo_grade = get_object_or_404(TipoGrade, id=tipo_grade_id, empresa=empresa)
        
        # Buscar valores associados a este tipo de grade
        valores = ValorGrade.objects.filter(
            tipo_grade=tipo_grade,
            ativo=True
        ).order_by('ordem', 'valor')
        
        # Preparar dados de resposta
        dados_valores = []
        for valor in valores:
            dados_valores.append({
                'id': valor.id,
                'valor': valor.valor,
                'descricao': valor.descricao,
                'ordem': valor.ordem
            })
        
        # Preparar exemplos baseados no tipo
        exemplos = []
        if tipo_grade.tipo == 'NUMEROS':
            exemplos = ['36', '38', '40', '42', '44', '46', '48', '50', '52']
        elif tipo_grade.tipo == 'LETRAS':
            exemplos = ['PP', 'P', 'M', 'G', 'GG', 'XG', 'XXG']
        elif tipo_grade.tipo == 'IDADE':
            exemplos = ['2', '4', '6', '8', '10', '12', '14', '16']
        elif tipo_grade.tipo == 'PERSONALIZADO':
            exemplos = ['Personalizado conforme necessidade']
        
        return JsonResponse({
            'success': True,
            'tipo_grade': {
                'id': tipo_grade.id,
                'nome': tipo_grade.nome,
                'tipo': tipo_grade.tipo,
                'descricao': tipo_grade.descricao
            },
            'valores': dados_valores,
            'exemplos': exemplos,
            'tem_valores': len(dados_valores) > 0
        })
        
    except TipoGrade.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Tipo de grade não encontrado'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# === VIEWS AJAX PARA MATÉRIAS-PRIMAS ===
@login_required
@require_empresa
def api_materia_prima_dados(request, materia_prima_id):
    """API para buscar dados da matéria-prima selecionada"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Requisição inválida'}, status=400)
    
    try:
        from apps.estoque.models import MateriaPrima
        
        empresa = get_current_empresa()
        materia_prima = get_object_or_404(
            MateriaPrima, 
            id=materia_prima_id, 
            empresa=empresa,
            ativo=True
        )
        
        return JsonResponse({
            'success': True,
            'materia_prima': {
                'id': materia_prima.id,
                'codigo': materia_prima.codigo,
                'descricao': materia_prima.descricao,
                'unidade': materia_prima.unidade,
                'unidade_display': materia_prima.get_unidade_display(),
                'custo_ultima_compra': float(materia_prima.custo_ultima_compra),
                'custo_medio_ponderado': float(materia_prima.custo_medio_ponderado),
                'quantidade_estoque': float(materia_prima.quantidade_em_estoque),
                'status_estoque': materia_prima.status_estoque,
                'status_estoque_display': materia_prima.status_estoque_display,
                'status_estoque_cor': materia_prima.status_estoque_cor,
                'necessita_reposicao': materia_prima.necessita_reposicao,
                'categoria': materia_prima.categoria.nome if materia_prima.categoria else None,
                'fornecedor': str(materia_prima.fornecedor_preferencial) if materia_prima.fornecedor_preferencial else None
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_empresa
def api_calcular_custo_produto(request):
    """API para calcular custo total do produto baseado nas matérias-primas"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Requisição inválida'}, status=400)
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método não permitido'}, status=405)
    
    try:
        import json
        from apps.estoque.models import MateriaPrima
        from decimal import Decimal
        
        empresa = get_current_empresa()
        data = json.loads(request.body)
        
        materias_primas = data.get('materias_primas', [])
        
        if not materias_primas:
            return JsonResponse({
                'success': True,
                'custo_total': 0,
                'detalhes': [],
                'margem_sugerida_40': 0,
                'margem_sugerida_50': 0
            })
        
        custo_total = Decimal('0.0000')
        detalhes = []
        
        for item in materias_primas:
            materia_prima_id = item.get('materia_prima_id')
            quantidade = Decimal(str(item.get('quantidade', 0)))
            
            if materia_prima_id and quantidade > 0:
                try:
                    materia_prima = MateriaPrima.objects.get(
                        id=materia_prima_id,
                        empresa=empresa,
                        ativo=True
                    )
                    
                    # Usar custo da última compra ou custo médio ponderado
                    custo_unitario = materia_prima.custo_ultima_compra or materia_prima.custo_medio_ponderado
                    custo_item = quantidade * custo_unitario
                    custo_total += custo_item
                    
                    detalhes.append({
                        'materia_prima_id': materia_prima.id,
                        'codigo': materia_prima.codigo,
                        'descricao': materia_prima.descricao,
                        'quantidade': float(quantidade),
                        'unidade': materia_prima.get_unidade_display(),
                        'custo_unitario': float(custo_unitario),
                        'custo_total_item': float(custo_item)
                    })
                    
                except MateriaPrima.DoesNotExist:
                    continue
        
        # Calcular margens sugeridas
        margem_40 = custo_total / Decimal('0.6')  # 40% de margem
        margem_50 = custo_total / Decimal('0.5')  # 50% de margem
        
        return JsonResponse({
            'success': True,
            'custo_total': float(custo_total),
            'detalhes': detalhes,
            'margem_sugerida_40': float(margem_40),
            'margem_sugerida_50': float(margem_50),
            'total_itens': len(detalhes)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Dados inválidos'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_empresa
def criar_materia_prima_rapida(request):
    """Cria nova matéria-prima via modal com campos essenciais"""
    if request.method == 'POST':
        try:
            from apps.estoque.models import MateriaPrima, CategoriaMateriaPrima
            
            empresa = get_current_empresa()
            
            codigo = request.POST.get('codigo', '').strip()
            descricao = request.POST.get('descricao', '').strip()
            unidade = request.POST.get('unidade', 'UN')
            custo_ultima_compra = request.POST.get('custo_ultima_compra', '0')
            categoria_id = request.POST.get('categoria_id')
            
            # Validações básicas
            if not descricao:
                return JsonResponse({
                    'success': False,
                    'error': 'Descrição da matéria-prima é obrigatória'
                }, status=400)
            
            # Gerar código automático se não fornecido
            if not codigo:
                ultimo_codigo = MateriaPrima.objects.filter(
                    empresa=empresa,
                    codigo__startswith='MP'
                ).order_by('-codigo').first()
                
                if ultimo_codigo:
                    try:
                        ultimo_numero = int(ultimo_codigo.codigo.replace('MP', ''))
                        proximo_numero = ultimo_numero + 1
                    except (ValueError, TypeError):
                        proximo_numero = 1
                else:
                    proximo_numero = 1
                
                codigo = f"MP{proximo_numero:03d}"
                
                # Verificar se código já existe
                while MateriaPrima.objects.filter(empresa=empresa, codigo=codigo).exists():
                    proximo_numero += 1
                    codigo = f"MP{proximo_numero:03d}"
            
            # Verificar se código já existe
            if MateriaPrima.objects.filter(empresa=empresa, codigo=codigo).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Já existe uma matéria-prima com este código'
                }, status=400)
            
            # Validar custo
            try:
                custo_ultima_compra = float(custo_ultima_compra)
                if custo_ultima_compra < 0:
                    raise ValueError("Custo deve ser positivo")
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': 'Custo deve ser um número válido'
                }, status=400)
            
            # Buscar categoria se fornecida
            categoria = None
            if categoria_id:
                try:
                    categoria = CategoriaMateriaPrima.objects.get(
                        id=categoria_id,
                        empresa=empresa
                    )
                except CategoriaMateriaPrima.DoesNotExist:
                    pass
            
            # Criar matéria-prima
            materia_prima = MateriaPrima.objects.create(
                empresa=empresa,
                codigo=codigo,
                descricao=descricao,
                unidade=unidade,
                custo_ultima_compra=custo_ultima_compra,
                custo_medio_ponderado=custo_ultima_compra,
                categoria=categoria,
                ativo=True
            )
            
            return JsonResponse({
                'success': True,
                'materia_prima': {
                    'id': materia_prima.id,
                    'codigo': materia_prima.codigo,
                    'descricao': materia_prima.descricao,
                    'display': f"{materia_prima.codigo} - {materia_prima.descricao}",
                    'unidade': materia_prima.get_unidade_display(),
                    'custo_ultima_compra': float(materia_prima.custo_ultima_compra)
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({'success': False, 'error': 'Método não permitido'}, status=405)


@login_required
@require_empresa
def api_categorias_materia_prima(request):
    """API para buscar categorias de matéria-prima"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Requisição inválida'}, status=400)
    
    try:
        from apps.estoque.models import CategoriaMateriaPrima
        
        empresa = get_current_empresa()
        
        categorias = CategoriaMateriaPrima.objects.filter(
            empresa=empresa,
            ativo=True
        ).order_by('nome')
        
        categorias_data = []
        for categoria in categorias:
            categorias_data.append({
                'id': categoria.id,
                'nome': categoria.nome,
                'descricao': categoria.descricao or '',
            })
        
        return JsonResponse({
            'success': True,
            'categorias': categorias_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erro ao buscar categorias: {str(e)}'
        }, status=500)
