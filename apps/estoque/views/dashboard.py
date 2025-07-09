from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from apps.core.middleware import require_empresa, get_current_empresa
from apps.core.mixins import TenantMixin
from ..models import (
    MateriaPrima, 
    MovimentacaoEstoque, 
    TipoMovimentacao, 
    InventarioFisico, 
    StatusInventario,
    LoteMateriaPrima
)
from ..services import EstoqueService


@method_decorator([login_required, require_empresa], name='dispatch')
class EstoqueDashboardView(TenantMixin, TemplateView):
    """Dashboard principal do módulo de estoque"""
    template_name = 'estoque/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        empresa = get_current_empresa()
        
        # === INDICADORES PRINCIPAIS ===
        materias_primas = MateriaPrima.objects.filter(empresa=empresa, ativo=True)
        
        # Contadores básicos
        total_materias = materias_primas.count()
        materias_ativas = materias_primas.filter(ativo=True).count()
        
        # Status do estoque
        status_counts = {'zerado': 0, 'baixo': 0, 'normal': 0, 'alto': 0}
        valor_total_estoque = Decimal('0.00')
        materias_baixo_estoque = []
        
        for mp in materias_primas:
            status = mp.status_estoque
            if status in status_counts:
                status_counts[status] += 1
            
            valor_total_estoque += mp.valor_total_em_estoque
            
            if status in ['zerado', 'baixo']:
                materias_baixo_estoque.append(mp)
        
        # === MOVIMENTAÇÕES RECENTES ===
        data_limite = timezone.now() - timedelta(days=30)
        movimentacoes_recentes = MovimentacaoEstoque.objects.filter(
            empresa=empresa,
            data_movimento__gte=data_limite,
            cancelada=False
        ).order_by('-data_movimento')[:10]
        
        # Estatísticas de movimentação
        total_entradas = MovimentacaoEstoque.objects.filter(
            empresa=empresa,
            tipo_movimento__in=TipoMovimentacao.get_entradas(),
            data_movimento__gte=data_limite,
            cancelada=False
        ).count()
        
        total_saidas = MovimentacaoEstoque.objects.filter(
            empresa=empresa,
            tipo_movimento__in=TipoMovimentacao.get_saidas(),
            data_movimento__gte=data_limite,
            cancelada=False
        ).count()
        
        # === INVENTÁRIOS ===
        inventarios_pendentes = InventarioFisico.objects.filter(
            empresa=empresa,
            status__in=[StatusInventario.ABERTO, StatusInventario.EM_ANDAMENTO]
        ).count()
        
        ultimo_inventario = InventarioFisico.objects.filter(
            empresa=empresa,
            status=StatusInventario.FINALIZADO
        ).order_by('-data_finalizacao').first()
        
        # === LOTES ===
        # Lotes próximos ao vencimento (30 dias)
        data_vencimento_limite = timezone.now().date() + timedelta(days=30)
        lotes_vencimento = LoteMateriaPrima.objects.filter(
            empresa=empresa,
            data_validade__lte=data_vencimento_limite,
            data_validade__gte=timezone.now().date(),
            status='ATIVO'
        ).order_by('data_validade')[:5]
        
        # Lotes vencidos
        lotes_vencidos = LoteMateriaPrima.objects.filter(
            empresa=empresa,
            data_validade__lt=timezone.now().date(),
            status='ATIVO'
        ).count()
        
        # === GRÁFICOS ===
        # Dados para gráfico de movimentações dos últimos 7 dias
        movimentacoes_graficos = []
        for i in range(7):
            data = timezone.now().date() - timedelta(days=i)
            entradas = MovimentacaoEstoque.objects.filter(
                empresa=empresa,
                data_movimento__date=data,
                tipo_movimento__in=TipoMovimentacao.get_entradas(),
                cancelada=False
            ).count()
            saidas = MovimentacaoEstoque.objects.filter(
                empresa=empresa,
                data_movimento__date=data,
                tipo_movimento__in=TipoMovimentacao.get_saidas(),
                cancelada=False
            ).count()
            
            movimentacoes_graficos.append({
                'data': data.strftime('%d/%m'),
                'entradas': entradas,
                'saidas': saidas
            })
        
        # Inverter para ordem cronológica
        movimentacoes_graficos.reverse()
        
        # === ALERTAS ===
        alertas = []
        
        # Alertas de estoque baixo
        if materias_baixo_estoque:
            alertas.append({
                'tipo': 'warning',
                'icone': 'fas fa-exclamation-triangle',
                'titulo': f'{len(materias_baixo_estoque)} matéria(s)-prima(s) com estoque baixo',
                'mensagem': 'Algumas matérias-primas precisam de reposição',
                'link': '/estoque/materias-primas/?status=baixo',
                'link_texto': 'Ver detalhes'
            })
        
        # Alertas de lotes vencidos
        if lotes_vencidos > 0:
            alertas.append({
                'tipo': 'danger',
                'icone': 'fas fa-calendar-times',
                'titulo': f'{lotes_vencidos} lote(s) vencido(s)',
                'mensagem': 'Lotes vencidos precisam ser removidos do estoque',
                'link': '/estoque/lotes/?status=vencido',
                'link_texto': 'Ver lotes'
            })
        
        # Alertas de inventário pendente
        if inventarios_pendentes > 0:
            alertas.append({
                'tipo': 'info',
                'icone': 'fas fa-clipboard-list',
                'titulo': f'{inventarios_pendentes} inventário(s) pendente(s)',
                'mensagem': 'Inventários em andamento precisam ser finalizados',
                'link': '/estoque/inventarios/',
                'link_texto': 'Ver inventários'
            })
        
        context.update({
            # Indicadores principais
            'total_materias': total_materias,
            'materias_ativas': materias_ativas,
            'valor_total_estoque': valor_total_estoque,
            'status_counts': status_counts,
            
            # Movimentações
            'movimentacoes_recentes': movimentacoes_recentes,
            'total_entradas': total_entradas,
            'total_saidas': total_saidas,
            'movimentacoes_graficos': movimentacoes_graficos,
            
            # Inventários
            'inventarios_pendentes': inventarios_pendentes,
            'ultimo_inventario': ultimo_inventario,
            
            # Lotes
            'lotes_vencimento': lotes_vencimento,
            'lotes_vencidos': lotes_vencidos,
            
            # Alertas
            'alertas': alertas,
            'materias_baixo_estoque': materias_baixo_estoque[:5],  # Primeiros 5
        })
        
        return context 