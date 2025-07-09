from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum, F

from .models import ProdutoMateriaPrima, Produto


@receiver([post_save, post_delete], sender=ProdutoMateriaPrima)
def atualizar_custo_produto(sender, instance, **kwargs):
    """
    Atualiza o campo custo_total_materias_primas do Produto sempre que um
    item da sua ficha técnica (ProdutoMateriaPrima) é salvo ou deletado.
    """
    produto = instance.produto

    # Calcula o custo total somando (quantidade * custo da matéria-prima)
    # para todos os itens da ficha técnica.
    # Usamos F() para acessar o valor do campo relacionado diretamente no DB.
    custo_total = produto.materias_primas.aggregate(
        total=Sum(F('quantidade') * F('materia_prima__custo_medio_ponderado'),
                    output_field=models.DecimalField())
    )['total'] or 0

    # Atualiza o campo no modelo Produto
    Produto.objects.filter(pk=produto.pk).update(
        custo_total_materias_primas=custo_total
    )

    print(f"✅ Custo de matérias-primas do Produto '{produto}' atualizado para: {custo_total}") 