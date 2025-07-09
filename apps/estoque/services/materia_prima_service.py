from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum

from ..models import MateriaPrima, TipoMovimentacao


def get_movimentacoes_recentes(materia_prima: MateriaPrima, dias: int = 30):
    """
    Busca as movimentações de uma matéria-prima nos últimos N dias.
    """
    data_limite = timezone.now() - timedelta(days=dias)
    return materia_prima.movimentacoes.filter(
        data_movimento__gte=data_limite
    ).order_by('-data_movimento')


def calcular_consumo_medio_diario(materia_prima: MateriaPrima, dias: int = 30):
    """
    Calcula o consumo médio diário de uma matéria-prima nos últimos N dias.
    """
    if dias <= 0:
        return 0

    data_limite = timezone.now() - timedelta(days=dias)

    # Tipos de movimentação que são consideradas 'consumo'
    tipos_de_saida = [
        TipoMovimentacao.SAIDA_PRODUCAO,
        TipoMovimentacao.SAIDA_VENDA,
        TipoMovimentacao.SAIDA_PERDA,
        TipoMovimentacao.SAIDA_CONSUMO,
    ]

    saidas = materia_prima.movimentacoes.filter(
        data_movimento__gte=data_limite,
        tipo_movimento__in=tipos_de_saida
    ).aggregate(total=Sum('quantidade'))['total'] or 0
    
    # Saídas são registradas com valor negativo, então usamos o valor absoluto.
    consumo_total = abs(saidas)
    
    return consumo_total / dias 