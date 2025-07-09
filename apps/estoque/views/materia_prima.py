from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator

from apps.core.middleware import require_empresa, get_current_empresa
from apps.core.mixins import TenantMixin
from ..models import MateriaPrima, CategoriaMateriaPrima, MovimentacaoEstoque
from ..forms import MateriaPrimaForm, CategoriaMateriaPrimaForm, FiltroEstoqueForm
from ..services import EstoqueService


@method_decorator([login_required, require_empresa], name='dispatch')
class MateriaPrimaListView(TenantMixin, ListView):
    """Lista de matérias-primas com filtros"""
    model = MateriaPrima
    template_name = 'estoque/materia_prima_list.html'
    context_object_name = 'materias_primas'
    paginate_by = 20

    def get_queryset(self):
        queryset = MateriaPrima.objects.filter(
            empresa=get_current_empresa(),
            ativo=True
        ).select_related('categoria', 'fornecedor_preferencial')
        
        # Aplicar filtros simples
        q = self.request.GET.get('q', '')
        categoria = self.request.GET.get('categoria', '')
        status = self.request.GET.get('status', '')
        fornecedor = self.request.GET.get('fornecedor', '')
        
        if q:
            queryset = queryset.filter(
                Q(codigo__icontains=q) |
                Q(descricao__icontains=q)
            )
        
        if categoria:
            queryset = queryset.filter(categoria_id=categoria)
        
        if fornecedor:
            queryset = queryset.filter(fornecedor_preferencial_id=fornecedor)
        
        # Filtrar por status de estoque (precisa ser feito depois)
        if status:
            materias_filtradas = []
            for mp in queryset:
                if mp.status_estoque == status:
                    materias_filtradas.append(mp.pk)
            queryset = queryset.filter(pk__in=materias_filtradas)
        
        return queryset.order_by('descricao')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa = get_current_empresa()
        
        # Estatísticas
        total_materias = MateriaPrima.objects.filter(empresa=empresa, ativo=True).count()
        
        # Contadores por status
        materias_zeradas = 0
        materias_baixas = 0
        materias_normais = 0
        materias_altas = 0
        
        for mp in MateriaPrima.objects.filter(empresa=empresa, ativo=True):
            status = mp.status_estoque
            if status == 'zerado':
                materias_zeradas += 1
            elif status == 'baixo':
                materias_baixas += 1
            elif status == 'normal':
                materias_normais += 1
            elif status == 'alto':
                materias_altas += 1
        
        # Dados para filtros
        categorias = CategoriaMateriaPrima.objects.filter(empresa=empresa, ativo=True).order_by('nome')
        
        try:
            from apps.cadastros.models import Fornecedor
            fornecedores = Fornecedor.objects.filter(empresa=empresa, ativo=True).order_by('razao_social')
        except ImportError:
            fornecedores = []
        
        context.update({
            'total_materias': total_materias,
            'materias_zeradas': materias_zeradas,
            'materias_baixas': materias_baixas,
            'materias_normais': materias_normais,
            'materias_altas': materias_altas,
            'categorias': categorias,
            'fornecedores': fornecedores,
        })
        
        return context


@method_decorator([login_required, require_empresa], name='dispatch')
class MateriaPrimaDetailView(TenantMixin, DetailView):
    """Detalhes de uma matéria-prima"""
    model = MateriaPrima
    template_name = 'estoque/materia_prima_detail.html'
    context_object_name = 'materia_prima'

    def get_queryset(self):
        return MateriaPrima.objects.filter(empresa=get_current_empresa())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        materia_prima = self.get_object()
        
        # Movimentações recentes
        movimentacoes = MovimentacaoEstoque.objects.filter(
            materia_prima=materia_prima,
            cancelada=False
        ).order_by('-data_movimento')[:50]
        
        context.update({
            'movimentacoes': movimentacoes,
            'estoque_atual': materia_prima.quantidade_em_estoque,
            'valor_total': materia_prima.valor_total_em_estoque,
            'status_estoque': materia_prima.status_estoque,
            'necessita_reposicao': materia_prima.necessita_reposicao,
        })
        
        return context


@method_decorator([login_required, require_empresa], name='dispatch')
class MateriaPrimaCreateView(TenantMixin, CreateView):
    """Criar nova matéria-prima"""
    model = MateriaPrima
    form_class = MateriaPrimaForm
    template_name = 'estoque/materia_prima_form.html'
    success_url = reverse_lazy('estoque:materia_prima_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['empresa'] = get_current_empresa()
        return kwargs

    def form_valid(self, form):
        form.instance.empresa = get_current_empresa()
        messages.success(self.request, 'Matéria-prima criada com sucesso!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = 'Nova Matéria-Prima'
        context['botao_submit'] = 'Criar Matéria-Prima'
        return context


@method_decorator([login_required, require_empresa], name='dispatch')
class MateriaPrimaUpdateView(TenantMixin, UpdateView):
    """Editar matéria-prima"""
    model = MateriaPrima
    form_class = MateriaPrimaForm
    template_name = 'estoque/materia_prima_form.html'
    success_url = reverse_lazy('estoque:materia_prima_list')

    def get_queryset(self):
        return MateriaPrima.objects.filter(empresa=get_current_empresa())

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['empresa'] = get_current_empresa()
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Matéria-prima atualizada com sucesso!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = f'Editar: {self.get_object().descricao}'
        context['botao_submit'] = 'Atualizar Matéria-Prima'
        return context


@method_decorator([login_required, require_empresa], name='dispatch')
class MateriaPrimaDeleteView(TenantMixin, DeleteView):
    """Excluir matéria-prima"""
    model = MateriaPrima
    template_name = 'estoque/materia_prima_confirm_delete.html'
    success_url = reverse_lazy('estoque:materia_prima_list')
    context_object_name = 'materia_prima'

    def get_queryset(self):
        return MateriaPrima.objects.filter(empresa=get_current_empresa())

    def delete(self, request, *args, **kwargs):
        materia_prima = self.get_object()
        
        # Verificar se há movimentações
        if materia_prima.movimentacoes.exists():
            messages.error(request, 
                f'Não é possível excluir a matéria-prima "{materia_prima.descricao}" '
                f'pois ela possui movimentações registradas. '
                f'Você pode desativá-la ao invés de excluí-la.')
            return redirect('estoque:materia_prima_list')
        
        nome = materia_prima.descricao
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'Matéria-prima "{nome}" excluída com sucesso!')
        return response


# Views para Categorias
@method_decorator([login_required, require_empresa], name='dispatch')
class CategoriaMateriaPrimaListView(TenantMixin, ListView):
    """Lista de categorias de matérias-primas"""
    model = CategoriaMateriaPrima
    template_name = 'estoque/categoria_list.html'
    context_object_name = 'categorias'
    paginate_by = 20

    def get_queryset(self):
        return CategoriaMateriaPrima.objects.filter(
            empresa=get_current_empresa()
        ).order_by('nome')


@method_decorator([login_required, require_empresa], name='dispatch')
class CategoriaMateriaPrimaCreateView(TenantMixin, CreateView):
    """Criar nova categoria"""
    model = CategoriaMateriaPrima
    form_class = CategoriaMateriaPrimaForm
    template_name = 'estoque/categoria_form.html'
    success_url = reverse_lazy('estoque:categoria_list')

    def form_valid(self, form):
        form.instance.empresa = get_current_empresa()
        
        # Se for requisição AJAX, retornar JSON
        if self.request.headers.get('X-CSRFToken'):
            categoria = form.save()
            return JsonResponse({
                'id': categoria.id,
                'nome': categoria.nome,
                'success': True
            })
        
        messages.success(self.request, 'Categoria criada com sucesso!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        # Se for requisição AJAX, retornar erro JSON
        if self.request.headers.get('X-CSRFToken'):
            errors = []
            for field, error_list in form.errors.items():
                for error in error_list:
                    errors.append(f"{field}: {error}")
            
            return JsonResponse({
                'error': '; '.join(errors),
                'success': False
            }, status=400)
        
        return super().form_invalid(form)


@method_decorator([login_required, require_empresa], name='dispatch')
class CategoriaMateriaPrimaUpdateView(TenantMixin, UpdateView):
    """Editar categoria"""
    model = CategoriaMateriaPrima
    form_class = CategoriaMateriaPrimaForm
    template_name = 'estoque/categoria_form.html'
    success_url = reverse_lazy('estoque:categoria_list')

    def get_queryset(self):
        return CategoriaMateriaPrima.objects.filter(empresa=get_current_empresa())

    def form_valid(self, form):
        messages.success(self.request, 'Categoria atualizada com sucesso!')
        return super().form_valid(form)


@method_decorator([login_required, require_empresa], name='dispatch')
class CategoriaMateriaPrimaDeleteView(TenantMixin, DeleteView):
    """Excluir categoria"""
    model = CategoriaMateriaPrima
    template_name = 'estoque/categoria_confirm_delete.html'
    success_url = reverse_lazy('estoque:categoria_list')
    context_object_name = 'categoria'

    def get_queryset(self):
        return CategoriaMateriaPrima.objects.filter(empresa=get_current_empresa())

    def delete(self, request, *args, **kwargs):
        categoria = self.get_object()
        
        # Verificar se há matérias-primas usando esta categoria
        if categoria.materiaprima_set.exists():
            messages.error(request, 
                f'Não é possível excluir a categoria "{categoria.nome}" '
                f'pois ela está sendo usada por matérias-primas.')
            return redirect('estoque:categoria_list')
        
        nome = categoria.nome
        response = super().delete(request, *args, **kwargs)
        messages.success(request, f'Categoria "{nome}" excluída com sucesso!')
        return response


# Views AJAX
@login_required
def buscar_materias_primas_ajax(request):
    """Busca matérias-primas via AJAX para select2"""
    empresa = request.user.empresa_atual
    busca = request.GET.get('q', '')
    
    materias = MateriaPrima.objects.filter(
        empresa=empresa,
        ativo=True
    )
    
    if busca:
        materias = materias.filter(
            Q(codigo__icontains=busca) |
            Q(descricao__icontains=busca)
        )
    
    materias = materias.order_by('descricao')[:20]
    
    results = []
    for mp in materias:
        results.append({
            'id': mp.pk,
            'text': f"{mp.codigo} - {mp.descricao}",
            'estoque': float(mp.quantidade_em_estoque),
            'unidade': mp.unidade,
            'status': mp.status_estoque
        })
    
    return JsonResponse({
        'results': results,
        'pagination': {'more': False}
    })


@login_required
def dashboard_estoque_ajax(request):
    """Dados para dashboard de estoque via AJAX"""
    empresa = request.user.empresa_atual
    
    # Estatísticas gerais
    total_materias = MateriaPrima.objects.filter(empresa=empresa, ativo=True).count()
    materias_baixo_estoque = []
    valor_total = 0
    
    for mp in MateriaPrima.objects.filter(empresa=empresa, ativo=True):
        if mp.status_estoque in ['zerado', 'baixo']:
            materias_baixo_estoque.append({
                'codigo': mp.codigo,
                'descricao': mp.descricao,
                'estoque_atual': float(mp.quantidade_em_estoque),
                'estoque_minimo': float(mp.estoque_minimo),
                'unidade': mp.unidade,
                'status': mp.status_estoque
            })
        valor_total += mp.valor_total_em_estoque
    
    return JsonResponse({
        'total_materias': total_materias,
        'materias_baixo_estoque': materias_baixo_estoque,
        'valor_total_estoque': float(valor_total),
        'alertas_count': len(materias_baixo_estoque)
    })


@login_required
@require_empresa
def gerar_codigo_materia_prima(request):
    """Gera código automático para matéria-prima"""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'error': 'Requisição inválida'}, status=400)
    
    empresa = get_current_empresa()
    
    # Buscar o último código usado
    ultima_materia = MateriaPrima.objects.filter(
        empresa=empresa,
        codigo__startswith='MP'
    ).order_by('-codigo').first()
    
    if ultima_materia:
        try:
            # Extrair número do último código (ex: MP001 -> 1)
            ultimo_numero = int(ultima_materia.codigo.replace('MP', ''))
            proximo_numero = ultimo_numero + 1
        except (ValueError, TypeError):
            # Se não conseguir extrair número, começar do 1
            proximo_numero = 1
    else:
        # Primeira matéria-prima
        proximo_numero = 1
    
    # Gerar código com 3 dígitos (MP001, MP002, etc.)
    novo_codigo = f"MP{proximo_numero:03d}"
    
    # Verificar se código já existe (segurança)
    while MateriaPrima.objects.filter(empresa=empresa, codigo=novo_codigo).exists():
        proximo_numero += 1
        novo_codigo = f"MP{proximo_numero:03d}"
    
    return JsonResponse({
        'codigo': novo_codigo,
        'numero': proximo_numero
    }) 