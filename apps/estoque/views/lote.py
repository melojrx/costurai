from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, View
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator

from apps.core.middleware import require_empresa, get_current_empresa
from apps.core.mixins import TenantMixin
from ..models import LoteMateriaPrima


@method_decorator([login_required, require_empresa], name='dispatch')
class LoteMateriaPrimaListView(TenantMixin, ListView):
    """Lista de lotes de matérias-primas"""
    model = LoteMateriaPrima
    template_name = 'estoque/lote_list.html'
    context_object_name = 'lotes'
    paginate_by = 20

    def get_queryset(self):
        queryset = LoteMateriaPrima.objects.filter(
            empresa=get_current_empresa()
        ).select_related('materia_prima', 'fornecedor').order_by('-data_entrada')
        
        # Aplicar filtros
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        materia_prima_id = self.request.GET.get('materia_prima')
        if materia_prima_id:
            queryset = queryset.filter(materia_prima_id=materia_prima_id)
        
        return queryset


@method_decorator([login_required, require_empresa], name='dispatch')
class LoteMateriaPrimaCreateView(TenantMixin, CreateView):
    """Criar novo lote"""
    model = LoteMateriaPrima
    template_name = 'estoque/lote_form.html'
    fields = [
        'materia_prima', 'numero_lote', 'lote_interno', 
        'data_fabricacao', 'data_validade', 'quantidade_inicial',
        'custo_unitario', 'numero_nota_fiscal', 'fornecedor',
        'localizacao', 'observacoes'
    ]
    success_url = reverse_lazy('estoque:lote_list')

    def form_valid(self, form):
        form.instance.empresa = get_current_empresa()
        messages.success(self.request, 'Lote criado com sucesso!')
        return super().form_valid(form)


@method_decorator([login_required, require_empresa], name='dispatch')
class LoteMateriaPrimaDetailView(TenantMixin, DetailView):
    """Detalhes do lote"""
    model = LoteMateriaPrima
    template_name = 'estoque/lote_detail.html'
    context_object_name = 'lote'

    def get_queryset(self):
        return LoteMateriaPrima.objects.filter(empresa=get_current_empresa())


@method_decorator([login_required, require_empresa], name='dispatch')
class BloquearLoteView(TenantMixin, View):
    """Bloquear lote"""
    
    def post(self, request, pk):
        try:
            lote = get_object_or_404(
                LoteMateriaPrima,
                pk=pk,
                empresa=get_current_empresa()
            )
            
            motivo = request.POST.get('motivo', '')
            lote.bloquear(motivo)
            
            messages.success(request, f'Lote "{lote.numero_lote}" bloqueado com sucesso!')
            
        except Exception as e:
            messages.error(request, f'Erro ao bloquear lote: {str(e)}')
        
        return redirect('estoque:lote_detail', pk=pk)


@method_decorator([login_required, require_empresa], name='dispatch')
class DesbloquearLoteView(TenantMixin, View):
    """Desbloquear lote"""
    
    def post(self, request, pk):
        try:
            lote = get_object_or_404(
                LoteMateriaPrima,
                pk=pk,
                empresa=get_current_empresa()
            )
            
            lote.desbloquear()
            messages.success(request, f'Lote "{lote.numero_lote}" desbloqueado com sucesso!')
            
        except Exception as e:
            messages.error(request, f'Erro ao desbloquear lote: {str(e)}')
        
        return redirect('estoque:lote_detail', pk=pk) 