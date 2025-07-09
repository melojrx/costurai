from apps.producao.models import ConsumoMateriaPrima

def copiar_ficha_tecnica_para_op(produto, ordem_producao):
    """
    Copia a ficha técnica (matérias-primas) de um Produto
    para uma Ordem de Produção específica.

    Args:
        produto (Produto): A instância do produto de origem.
        ordem_producao (OrdemProducao): A instância da OP de destino.
    """
    # Busca todos os itens da ficha técnica do produto
    ficha_tecnica = produto.materias_primas.all()

    if not ficha_tecnica.exists():
        print(f"⚠️ Produto '{produto}' não possui ficha técnica para copiar.")
        return

    # Limpa consumos antigos da OP, caso existam (para edições)
    ordem_producao.materias_primas.all().delete()

    # Cria novos registros de consumo para a OP
    novos_consumos = []
    for item_ficha in ficha_tecnica:
        novos_consumos.append(
            ConsumoMateriaPrima(
                ordem_producao=ordem_producao,
                materia_prima=item_ficha.materia_prima,
                quantidade_necessaria=item_ficha.quantidade
            )
        )
    
    # Usa bulk_create para performance, inserindo todos de uma vez
    if novos_consumos:
        ConsumoMateriaPrima.objects.bulk_create(novos_consumos)
        print(f"✅ Ficha técnica de '{produto}' copiada para a OP '{ordem_producao}'.") 