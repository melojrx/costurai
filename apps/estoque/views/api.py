from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.core.middleware import require_empresa, get_current_empresa
from ..models import MateriaPrima, LoteMateriaPrima


@login_required
@require_empresa
@require_http_methods(["GET"])
def listar_materias_primas_json(request):
    """API para listar matérias-primas em formato JSON"""
    empresa = get_current_empresa()
    
    materias_primas = MateriaPrima.objects.filter(
        empresa=empresa,
        ativo=True
    ).values(
        'id', 'codigo', 'descricao', 'unidade',
        'quantidade_em_estoque', 'estoque_minimo', 'estoque_maximo',
        'custo_medio_ponderado'
    )
    
    return JsonResponse({
        'materias_primas': list(materias_primas)
    })


@login_required
@require_empresa
@require_http_methods(["GET"])
def verificar_estoque_json(request, pk):
    """API para verificar estoque de uma matéria-prima"""
    empresa = get_current_empresa()
    
    materia_prima = get_object_or_404(
        MateriaPrima,
        pk=pk,
        empresa=empresa
    )
    
    return JsonResponse({
        'id': materia_prima.id,
        'codigo': materia_prima.codigo,
        'descricao': materia_prima.descricao,
        'quantidade_em_estoque': float(materia_prima.quantidade_em_estoque),
        'estoque_minimo': float(materia_prima.estoque_minimo),
        'status_estoque': materia_prima.status_estoque,
        'custo_medio': float(materia_prima.custo_medio_ponderado),
        'valor_total': float(materia_prima.valor_total_em_estoque),
    })


@login_required
@require_empresa
@require_http_methods(["GET"])
def materia_prima_detail_json(request, pk):
    """API para detalhes de uma matéria-prima (usado no formulário de entrada)"""
    empresa = get_current_empresa()
    
    materia_prima = get_object_or_404(
        MateriaPrima,
        pk=pk,
        empresa=empresa
    )
    
    return JsonResponse({
        'id': materia_prima.id,
        'codigo': materia_prima.codigo,
        'descricao': materia_prima.descricao,
        'unidade': materia_prima.unidade,
        'quantidade_em_estoque': float(materia_prima.quantidade_em_estoque),
        'estoque_minimo': float(materia_prima.estoque_minimo),
        'estoque_maximo': float(materia_prima.estoque_maximo),
        'custo_medio_ponderado': f"{float(materia_prima.custo_medio_ponderado):.2f}",
        'status_estoque': materia_prima.status_estoque,
        'valor_total': float(materia_prima.valor_total_em_estoque),
    })


@login_required
@require_empresa
@require_http_methods(["GET"])
def dashboard_data_json(request):
    """API para dados do dashboard em tempo real"""
    empresa = get_current_empresa()
    
    # Contadores básicos
    total_materias = MateriaPrima.objects.filter(empresa=empresa, ativo=True).count()
    
    # Status do estoque
    materias_primas = MateriaPrima.objects.filter(empresa=empresa, ativo=True)
    status_counts = {'zerado': 0, 'baixo': 0, 'normal': 0, 'alto': 0}
    
    for mp in materias_primas:
        status = mp.status_estoque
        if status in status_counts:
            status_counts[status] += 1
    
    return JsonResponse({
        'total_materias': total_materias,
        'status_counts': status_counts,
        'timestamp': timezone.now().isoformat(),
    })


@login_required
@require_empresa
@require_http_methods(["GET"])
def alertas_estoque_json(request):
    """API para alertas de estoque"""
    empresa = get_current_empresa()
    
    # Matérias-primas com estoque baixo
    materias_baixo = MateriaPrima.objects.filter(
        empresa=empresa,
        ativo=True
    )
    
    alertas = []
    for mp in materias_baixo:
        if mp.status_estoque in ['zerado', 'baixo']:
            alertas.append({
                'tipo': 'estoque_baixo',
                'materia_prima_id': mp.id,
                'codigo': mp.codigo,
                'descricao': mp.descricao,
                'estoque_atual': float(mp.quantidade_em_estoque),
                'estoque_minimo': float(mp.estoque_minimo),
                'status': mp.status_estoque,
            })
    
    return JsonResponse({
        'alertas': alertas,
        'total': len(alertas),
    })


@login_required
@require_empresa
@require_http_methods(["GET"])
def listar_lotes_json(request, materia_prima_id):
    """API para listar lotes de uma matéria-prima"""
    empresa = get_current_empresa()
    
    # Verificar se a matéria-prima existe e pertence à empresa
    materia_prima = get_object_or_404(
        MateriaPrima,
        pk=materia_prima_id,
        empresa=empresa
    )
    
    lotes = LoteMateriaPrima.objects.filter(
        materia_prima=materia_prima,
        status='ATIVO'
    ).values(
        'id', 'numero_lote', 'data_validade', 
        'quantidade_disponivel', 'bloqueado'
    ).order_by('data_validade')
    
    return JsonResponse({
        'lotes': list(lotes),
        'materia_prima': {
            'id': materia_prima.id,
            'codigo': materia_prima.codigo,
            'descricao': materia_prima.descricao,
        }
    }) 