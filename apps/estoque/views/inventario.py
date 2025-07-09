from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, View
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.db.models import Sum, Count
from decimal import Decimal

from apps.core.middleware import require_empresa, get_current_empresa
from apps.core.mixins import TenantMixin
from ..models import InventarioFisico, ItemInventario, StatusInventario
from ..models.materia_prima import MateriaPrima
from ..models.materia_prima import CategoriaMateriaPrima
from ..services import InventarioService


@method_decorator([login_required, require_empresa], name='dispatch')
class InventarioFisicoListView(TenantMixin, ListView):
    """Lista de inventários físicos"""
    model = InventarioFisico
    template_name = 'estoque/inventario_list.html'
    context_object_name = 'inventarios'
    paginate_by = 20

    def get_queryset(self):
        return InventarioFisico.objects.filter(
            empresa=get_current_empresa()
        ).order_by('-data_abertura')


@method_decorator([login_required, require_empresa], name='dispatch')
class InventarioFisicoCreateView(TenantMixin, CreateView):
    """Criar novo inventário"""
    model = InventarioFisico
    template_name = 'estoque/inventario_form.html'
    fields = ['descricao', 'categoria_filtro', 'incluir_zerados']
    success_url = reverse_lazy('estoque:inventario_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorias'] = CategoriaMateriaPrima.objects.filter(
            empresa=get_current_empresa(),
            ativo=True
        ).order_by('nome')
        return context

    def form_valid(self, form):
        try:
            # Usar o service para criar o inventário
            inventario = InventarioService.criar_inventario(
                empresa=get_current_empresa(),
                descricao=form.cleaned_data['descricao'],
                responsavel=self.request.user,
                categoria_filtro=form.cleaned_data.get('categoria_filtro'),
                incluir_zerados=form.cleaned_data.get('incluir_zerados', False)
            )
            
            messages.success(
                self.request, 
                f'Inventário "{inventario.numero}" criado com sucesso! '
                f'{inventario.itens.count()} itens foram adicionados.'
            )
            return redirect('estoque:inventario_detail', pk=inventario.pk)
            
        except Exception as e:
            messages.error(self.request, f'Erro ao criar inventário: {str(e)}')
            return self.form_invalid(form)


@method_decorator([login_required, require_empresa], name='dispatch')
class ResumoInventarioAPIView(TenantMixin, View):
    """API para obter resumo estimado do inventário baseado nos filtros"""
    
    def get(self, request):
        try:
            categoria_id = request.GET.get('categoria_filtro')
            incluir_zerados = request.GET.get('incluir_zerados') == 'true'
            
            empresa = get_current_empresa()
            
            # Query base das matérias-primas
            materias = MateriaPrima.objects.filter(
                empresa=empresa,
                ativo=True
            )
            
            # Aplicar filtro de categoria
            if categoria_id:
                materias = materias.filter(categoria_id=categoria_id)
            
            # Aplicar filtro de estoque zerado
            if not incluir_zerados:
                # Filtrar apenas com estoque > 0
                materias = materias.filter(quantidade_em_estoque__gt=0)
            
            # Calcular estatísticas
            total_itens = materias.count()
            
            # Contar categorias únicas
            if categoria_id:
                total_categorias = 1
            else:
                total_categorias = materias.values('categoria').distinct().count()
            
            # Calcular valor total estimado
            valor_total = Decimal('0.00')
            for materia in materias:
                valor_total += materia.valor_total_em_estoque or Decimal('0.00')
            
            # Estimar tempo baseado em 20 itens por hora
            tempo_estimado_horas = max(1, total_itens // 20) if total_itens > 0 else 0
            
            return JsonResponse({
                'total_itens': total_itens,
                'total_categorias': total_categorias,
                'valor_estimado': float(valor_total),
                'tempo_estimado_horas': tempo_estimado_horas,
                'status': 'success'
            })
            
        except Exception as e:
            return JsonResponse({
                'error': str(e),
                'status': 'error'
            }, status=500)


@method_decorator([login_required, require_empresa], name='dispatch')
class InventarioFisicoDetailView(TenantMixin, DetailView):
    """Detalhes do inventário"""
    model = InventarioFisico
    template_name = 'estoque/inventario_detail.html'
    context_object_name = 'inventario'

    def get_queryset(self):
        return InventarioFisico.objects.filter(empresa=get_current_empresa())


@method_decorator([login_required, require_empresa], name='dispatch')
class IniciarInventarioView(TenantMixin, View):
    """Iniciar inventário"""
    
    def post(self, request, pk):
        try:
            inventario = get_object_or_404(
                InventarioFisico,
                pk=pk,
                empresa=get_current_empresa()
            )
            
            InventarioService.iniciar_inventario(inventario)
            messages.success(request, f'Inventário "{inventario.numero}" iniciado com sucesso!')
            
        except Exception as e:
            messages.error(request, f'Erro ao iniciar inventário: {str(e)}')
        
        return redirect('estoque:inventario_detail', pk=pk)


@method_decorator([login_required, require_empresa], name='dispatch')
class FinalizarInventarioView(TenantMixin, View):
    """Finalizar inventário"""
    
    def post(self, request, pk):
        try:
            inventario = get_object_or_404(
                InventarioFisico,
                pk=pk,
                empresa=get_current_empresa()
            )
            
            gerar_ajustes = request.POST.get('gerar_ajustes') == 'true'
            resumo = InventarioService.finalizar_inventario(
                inventario, 
                gerar_ajustes=gerar_ajustes,
                usuario=request.user
            )
            
            messages.success(
                request, 
                f'Inventário "{inventario.numero}" finalizado! '
                f'{resumo["total_ajustes"]} ajustes gerados.'
            )
            
        except Exception as e:
            messages.error(request, f'Erro ao finalizar inventário: {str(e)}')
        
        return redirect('estoque:inventario_detail', pk=pk)


@method_decorator([login_required, require_empresa], name='dispatch')
class CancelarInventarioView(TenantMixin, View):
    """Cancelar inventário"""
    
    def post(self, request, pk):
        try:
            inventario = get_object_or_404(
                InventarioFisico,
                pk=pk,
                empresa=get_current_empresa()
            )
            
            motivo = request.POST.get('motivo', '')
            InventarioService.cancelar_inventario(inventario, motivo)
            
            messages.success(request, f'Inventário "{inventario.numero}" cancelado.')
            
        except Exception as e:
            messages.error(request, f'Erro ao cancelar inventário: {str(e)}')
        
        return redirect('estoque:inventario_detail', pk=pk)


@method_decorator([login_required, require_empresa], name='dispatch')
class ContarItemInventarioView(TenantMixin, View):
    """Registrar contagem de item"""
    
    def post(self, request, pk, item_pk):
        try:
            inventario = get_object_or_404(
                InventarioFisico,
                pk=pk,
                empresa=get_current_empresa()
            )
            
            item = get_object_or_404(
                ItemInventario,
                pk=item_pk,
                inventario=inventario
            )
            
            quantidade_fisica = float(request.POST.get('quantidade_fisica', 0))
            observacoes = request.POST.get('observacoes', '')
            
            InventarioService.registrar_contagem(
                item, 
                quantidade_fisica, 
                request.user, 
                observacoes
            )
            
            messages.success(request, 'Contagem registrada com sucesso!')
            
        except Exception as e:
            messages.error(request, f'Erro ao registrar contagem: {str(e)}')
        
        return redirect('estoque:inventario_detail', pk=pk) 