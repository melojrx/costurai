from django.utils import timezone
from .models import OrdemProducao


def gerar_proximo_numero_op(empresa_id: int) -> str:
    """
    Gera o próximo número sequencial para uma Ordem de Produção
    no formato OP-ANO-XXXX.
    """
    ano_atual = timezone.now().year
    
    # Filtra as OPs da empresa que começam com o prefixo do ano atual
    ultima_op = OrdemProducao.objects.filter(
        empresa_id=empresa_id, 
        numero_op__startswith=f'OP-{ano_atual}'
    ).order_by('numero_op').last()
    
    novo_num = 1
    if ultima_op:
        try:
            # Extrai o último número da sequência
            ultimo_num_str = ultima_op.numero_op.split('-')[-1]
            novo_num = int(ultimo_num_str) + 1
        except (ValueError, IndexError):
            # Caso o formato seja inesperado, recomeça do 1
            novo_num = 1
            
    return f"OP-{ano_atual}-{novo_num:04d}"
