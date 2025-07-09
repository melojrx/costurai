from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta

from apps.core.middleware import require_empresa, get_current_empresa
from apps.core.mixins import TenantMixin
from ..models import MateriaPrima, MovimentacaoEstoque, LoteMateriaPrima


@method_decorator([login_required, require_empresa], name='dispatch')
class RelatoriosEstoqueView(TenantMixin, TemplateView):
    """Dashboard de relatórios de estoque"""
    template_name = 'estoque/relatorios.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa = get_current_empresa()
        
        # Estatísticas básicas
        total_materias = MateriaPrima.objects.filter(empresa=empresa, ativo=True).count()
        total_movimentacoes = MovimentacaoEstoque.objects.filter(empresa=empresa).count()
        total_lotes = LoteMateriaPrima.objects.filter(empresa=empresa).count()
        
        context.update({
            'total_materias': total_materias,
            'total_movimentacoes': total_movimentacoes,
            'total_lotes': total_lotes,
        })
        
        return context


@method_decorator([login_required, require_empresa], name='dispatch')
class RelatorioEstoqueAtualView(TenantMixin, TemplateView):
    """Relatório de estoque atual"""
    template_name = 'estoque/relatorio_estoque_atual.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa = get_current_empresa()
        
        # Matérias-primas com estoque
        materias_primas = MateriaPrima.objects.filter(
            empresa=empresa, 
            ativo=True
        ).select_related('categoria').order_by('descricao')
        
        context['materias_primas'] = materias_primas
        return context


@method_decorator([login_required, require_empresa], name='dispatch')
class RelatorioMovimentacoesView(TenantMixin, TemplateView):
    """Relatório de movimentações"""
    template_name = 'estoque/relatorio_movimentacoes.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa = get_current_empresa()
        
        # Filtros
        data_inicio = self.request.GET.get('data_inicio')
        data_fim = self.request.GET.get('data_fim')
        
        # Movimentações do período
        movimentacoes = MovimentacaoEstoque.objects.filter(
            empresa=empresa,
            cancelada=False
        ).select_related('materia_prima', 'usuario')
        
        if data_inicio:
            movimentacoes = movimentacoes.filter(data_movimento__date__gte=data_inicio)
        if data_fim:
            movimentacoes = movimentacoes.filter(data_movimento__date__lte=data_fim)
        
        movimentacoes = movimentacoes.order_by('-data_movimento')[:100]
        
        context.update({
            'movimentacoes': movimentacoes,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
        })
        
        return context


@method_decorator([login_required, require_empresa], name='dispatch')
class RelatorioCustosView(TenantMixin, TemplateView):
    """Relatório de custos"""
    template_name = 'estoque/relatorio_custos.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa = get_current_empresa()
        
        # Matérias-primas com custos
        materias_primas = MateriaPrima.objects.filter(
            empresa=empresa, 
            ativo=True
        ).select_related('categoria').order_by('descricao')
        
        # Calcular valor total do estoque
        valor_total = sum(mp.valor_total_em_estoque for mp in materias_primas)
        
        context.update({
            'materias_primas': materias_primas,
            'valor_total_estoque': valor_total,
        })
        
        return context


@method_decorator([login_required, require_empresa], name='dispatch')
class RelatorioLotesVencimentoView(TenantMixin, TemplateView):
    """Relatório de lotes próximos ao vencimento"""
    template_name = 'estoque/relatorio_lotes_vencimento.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa = get_current_empresa()
        
        # Lotes próximos ao vencimento (30 dias)
        data_limite = timezone.now().date() + timedelta(days=30)
        lotes_vencimento = LoteMateriaPrima.objects.filter(
            empresa=empresa,
            data_validade__lte=data_limite,
            data_validade__gte=timezone.now().date(),
            status='ATIVO'
        ).select_related('materia_prima').order_by('data_validade')
        
        # Lotes vencidos
        lotes_vencidos = LoteMateriaPrima.objects.filter(
            empresa=empresa,
            data_validade__lt=timezone.now().date(),
            status='ATIVO'
        ).select_related('materia_prima').order_by('data_validade')
        
        context.update({
            'lotes_vencimento': lotes_vencimento,
            'lotes_vencidos': lotes_vencidos,
        })
        
        return context 