from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum

from .models import GradeProducao, OrdemProducao


@receiver([post_save, post_delete], sender=GradeProducao)
def atualizar_quantidade_total_op(sender, instance, **kwargs):
    """
    Atualiza o campo quantidade_total da Ordem de Produção sempre que
    uma GradeProducao é criada, alterada ou deletada.
    """
    ordem_producao = instance.ordem_producao

    # Usamos aggregate para calcular a soma total de forma eficiente no banco.
    resultado = ordem_producao.itens_grade.aggregate(
        total_grade=Sum('quantidade')
    )

    nova_quantidade = resultado['total_grade'] or 0

    # Atualizamos o campo usando update() para evitar recursão de signals
    OrdemProducao.objects.filter(pk=ordem_producao.pk).update(
        quantidade_total=nova_quantidade
    )
    
    print(f"✅ Quantidade total da OP '{ordem_producao}' atualizada para: {nova_quantidade}") 