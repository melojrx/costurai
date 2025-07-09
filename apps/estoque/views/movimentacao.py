from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, View
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.utils import timezone

from apps.core.middleware import require_empresa, get_current_empresa
from apps.core.mixins import TenantMixin
from ..models import (
    MovimentacaoEstoque, 
    MateriaPrima, 
    TipoMovimentacao,
    LoteMateriaPrima
)
from ..forms import (
    MovimentacaoEstoqueForm,
    EntradaEstoqueForm,
    SaidaEstoqueForm,
    FiltroEstoqueForm
)
from ..services import EstoqueService


@method_decorator([login_required, require_empresa], name='dispatch')
class MovimentacaoEstoqueListView(TenantMixin, ListView):
    """Lista de movimentações de estoque (Kardex)"""
    model = MovimentacaoEstoque
    template_name = 'estoque/movimentacao_list.html'
    context_object_name = 'movimentacoes'
    paginate_by = 50

    def get_queryset(self):
        queryset = MovimentacaoEstoque.objects.filter(
            empresa=get_current_empresa()
        ).select_related('materia_prima', 'usuario', 'lote').order_by('-data_movimento')
        
        # Aplicar filtros
        materia_prima_id = self.request.GET.get('materia_prima')
        tipo_movimento = self.request.GET.get('tipo_movimento')
        data_inicio = self.request.GET.get('data_inicio')
        data_fim = self.request.GET.get('data_fim')
        apenas_canceladas = self.request.GET.get('canceladas')
        
        if materia_prima_id:
            queryset = queryset.filter(materia_prima_id=materia_prima_id)
        
        if tipo_movimento:
            queryset = queryset.filter(tipo_movimento=tipo_movimento)
        
        if data_inicio:
            queryset = queryset.filter(data_movimento__date__gte=data_inicio)
        
        if data_fim:
            queryset = queryset.filter(data_movimento__date__lte=data_fim)
        
        if apenas_canceladas == 'true':
            queryset = queryset.filter(cancelada=True)
        elif apenas_canceladas == 'false':
            queryset = queryset.filter(cancelada=False)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa = get_current_empresa()
        
        # Estatísticas
        total_movimentacoes = self.get_queryset().count()
        entradas = self.get_queryset().filter(
            tipo_movimento__in=TipoMovimentacao.get_entradas()
        ).count()
        saidas = self.get_queryset().filter(
            tipo_movimento__in=TipoMovimentacao.get_saidas()
        ).count()
        canceladas = self.get_queryset().filter(cancelada=True).count()
        
        context.update({
            'total_movimentacoes': total_movimentacoes,
            'total_entradas': entradas,
            'total_saidas': saidas,
            'total_canceladas': canceladas,
            'materias_primas': MateriaPrima.objects.filter(
                empresa=empresa, ativo=True
            ).order_by('descricao'),
            'tipos_movimento': TipoMovimentacao.choices,
        })
        
        return context


@method_decorator([login_required, require_empresa], name='dispatch')
class MovimentacaoEstoqueDetailView(TenantMixin, DetailView):
    """Detalhes de uma movimentação"""
    model = MovimentacaoEstoque
    template_name = 'estoque/movimentacao_detail.html'
    context_object_name = 'movimentacao'

    def get_queryset(self):
        return MovimentacaoEstoque.objects.filter(
            empresa=get_current_empresa()
        ).select_related('materia_prima', 'usuario', 'lote')


@method_decorator([login_required, require_empresa], name='dispatch')
class EntradaEstoqueCreateView(TenantMixin, CreateView):
    """Registrar entrada de estoque"""
    model = MovimentacaoEstoque
    form_class = EntradaEstoqueForm
    template_name = 'estoque/entrada_form.html'
    success_url = reverse_lazy('estoque:movimentacao_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['empresa'] = get_current_empresa()
        return kwargs

    def form_valid(self, form):
        try:
            # Usar o service para registrar a movimentação
            movimentacao = EstoqueService.registrar_movimentacao(
                empresa=get_current_empresa(),
                materia_prima=form.cleaned_data['materia_prima'],
                tipo_movimento=form.cleaned_data['tipo_movimento'],
                quantidade=form.cleaned_data['quantidade'],
                custo_unitario=form.cleaned_data['custo_unitario'],
                usuario=self.request.user,
                numero_documento=form.cleaned_data.get('numero_documento', ''),
                observacoes=form.cleaned_data.get('observacoes', ''),
                lote=form.cleaned_data.get('lote'),
            )
            
            messages.success(
                self.request, 
                f'Entrada registrada com sucesso! '
                f'{movimentacao.quantidade} {movimentacao.materia_prima.unidade} '
                f'de {movimentacao.materia_prima.descricao}'
            )
            return redirect(self.success_url)
            
        except Exception as e:
            messages.error(self.request, f'Erro ao registrar entrada: {str(e)}')
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Registrar Entrada de Estoque'
        context['tipo_operacao'] = 'entrada'
        return context


@method_decorator([login_required, require_empresa], name='dispatch')
class SaidaEstoqueCreateView(TenantMixin, CreateView):
    """Registrar saída de estoque"""
    model = MovimentacaoEstoque
    form_class = SaidaEstoqueForm
    template_name = 'estoque/saida_form.html'
    success_url = reverse_lazy('estoque:movimentacao_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['empresa'] = get_current_empresa()
        return kwargs

    def form_valid(self, form):
        try:
            # Usar o service para registrar a movimentação
            movimentacao = EstoqueService.registrar_movimentacao(
                empresa=get_current_empresa(),
                materia_prima=form.cleaned_data['materia_prima'],
                tipo_movimento=form.cleaned_data['tipo_movimento'],
                quantidade=form.cleaned_data['quantidade'],
                custo_unitario=form.cleaned_data.get('custo_unitario', 0),
                usuario=self.request.user,
                numero_documento=form.cleaned_data.get('numero_documento', ''),
                observacoes=form.cleaned_data.get('observacoes', ''),
                lote=form.cleaned_data.get('lote'),
            )
            
            messages.success(
                self.request, 
                f'Saída registrada com sucesso! '
                f'{abs(movimentacao.quantidade)} {movimentacao.materia_prima.unidade} '
                f'de {movimentacao.materia_prima.descricao}'
            )
            return redirect(self.success_url)
            
        except Exception as e:
            messages.error(self.request, f'Erro ao registrar saída: {str(e)}')
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Registrar Saída de Estoque'
        context['tipo_operacao'] = 'saida'
        return context


@method_decorator([login_required, require_empresa], name='dispatch')
class AjusteEstoqueCreateView(TenantMixin, CreateView):
    """Registrar ajuste de estoque"""
    model = MovimentacaoEstoque
    form_class = MovimentacaoEstoqueForm
    template_name = 'estoque/ajuste_form.html'
    success_url = reverse_lazy('estoque:movimentacao_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['empresa'] = get_current_empresa()
        return kwargs

    def form_valid(self, form):
        try:
            # Determinar tipo de ajuste baseado na quantidade
            quantidade = form.cleaned_data['quantidade']
            if quantidade > 0:
                tipo_movimento = TipoMovimentacao.ENTRADA_AJUSTE
            else:
                tipo_movimento = TipoMovimentacao.SAIDA_AJUSTE
            
            # Usar o service para registrar a movimentação
            movimentacao = EstoqueService.registrar_movimentacao(
                empresa=get_current_empresa(),
                materia_prima=form.cleaned_data['materia_prima'],
                tipo_movimento=tipo_movimento,
                quantidade=quantidade,
                custo_unitario=form.cleaned_data.get('custo_unitario', 0),
                usuario=self.request.user,
                numero_documento=form.cleaned_data.get('numero_documento', ''),
                observacoes=form.cleaned_data.get('observacoes', ''),
                motivo_ajuste=form.cleaned_data['motivo_ajuste'],
                lote=form.cleaned_data.get('lote'),
            )
            
            tipo_texto = 'Entrada' if quantidade > 0 else 'Saída'
            messages.success(
                self.request, 
                f'Ajuste registrado com sucesso! '
                f'{tipo_texto} de {abs(movimentacao.quantidade)} {movimentacao.materia_prima.unidade} '
                f'de {movimentacao.materia_prima.descricao}'
            )
            return redirect(self.success_url)
            
        except Exception as e:
            messages.error(self.request, f'Erro ao registrar ajuste: {str(e)}')
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Registrar Ajuste de Estoque'
        context['tipo_operacao'] = 'ajuste'
        return context


@method_decorator([login_required, require_empresa], name='dispatch')
class CancelarMovimentacaoView(TenantMixin, View):
    """Cancelar uma movimentação"""
    
    def post(self, request, pk):
        try:
            movimentacao = get_object_or_404(
                MovimentacaoEstoque,
                pk=pk,
                empresa=get_current_empresa()
            )
            
            if movimentacao.cancelada:
                messages.warning(request, 'Esta movimentação já está cancelada.')
                return redirect('estoque:movimentacao_detail', pk=pk)
            
            motivo = request.POST.get('motivo', '')
            if not motivo.strip():
                messages.error(request, 'Motivo do cancelamento é obrigatório.')
                return redirect('estoque:movimentacao_detail', pk=pk)
            
            # Cancelar usando o método do modelo
            movimentacao.cancelar(usuario=request.user, motivo=motivo)
            
            messages.success(
                request, 
                f'Movimentação cancelada com sucesso. '
                f'O estoque foi ajustado automaticamente.'
            )
            
        except Exception as e:
            messages.error(request, f'Erro ao cancelar movimentação: {str(e)}')
        
        return redirect('estoque:movimentacao_detail', pk=pk) 