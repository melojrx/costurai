from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.db.models import Sum
from decimal import Decimal

from .models import MovimentacaoEstoque, TipoMovimentacao, LoteMateriaPrima, MateriaPrima
from .services import CustoMedioService


@receiver(post_save, sender=MovimentacaoEstoque)
def atualizar_custo_medio_pos_movimentacao(sender, instance, created, **kwargs):
    """
    Atualiza o custo médio ponderado após uma movimentação de entrada
    """
    if created and not instance.cancelada:
        # Só recalcular para entradas
        if instance.tipo_movimento in TipoMovimentacao.get_entradas():
            CustoMedioService.recalcular_custo_medio(
                instance.materia_prima,
                abs(instance.quantidade),
                instance.custo_unitario
            )


@receiver(post_save, sender=MovimentacaoEstoque)
def atualizar_status_lote_pos_movimentacao(sender, instance, created, **kwargs):
    """
    Atualiza o status do lote após movimentação
    """
    if instance.lote and not instance.cancelada:
        instance.lote.atualizar_status()


@receiver(post_save, sender=MovimentacaoEstoque)
def log_movimentacao_estoque(sender, instance, created, **kwargs):
    """
    Log das movimentações para auditoria
    """
    if created:
        import logging
        logger = logging.getLogger('apps.estoque')
        
        logger.info(
            f"Movimentação criada: {instance.tipo_movimento} - "
            f"{instance.materia_prima.descricao} - "
            f"Qtd: {instance.quantidade} - "
            f"Usuário: {instance.usuario.username if instance.usuario else 'Sistema'}"
        )


@receiver(pre_save, sender=MovimentacaoEstoque)
def validar_movimentacao_antes_salvar(sender, instance, **kwargs):
    """
    Validações antes de salvar uma movimentação
    """
    # Validar se matéria-prima está ativa
    if not instance.materia_prima.ativo:
        raise ValueError("Não é possível movimentar matéria-prima inativa")
    
    # Validar lote se necessário
    if instance.materia_prima.controlar_lote:
        if instance.tipo_movimento in TipoMovimentacao.get_saidas() and not instance.lote:
            raise ValueError("Lote é obrigatório para saídas desta matéria-prima")
        
        if instance.lote and not instance.lote.pode_ser_utilizado:
            raise ValueError("Lote não pode ser utilizado (bloqueado, vencido ou esgotado)")


@receiver(post_delete, sender=MovimentacaoEstoque)
def recalcular_custo_apos_exclusao(sender, instance, **kwargs):
    """
    Recalcula o custo médio após exclusão de uma movimentação
    """
    if instance.tipo_movimento in TipoMovimentacao.get_entradas():
        CustoMedioService.recalcular_custo_medio_completo(instance.materia_prima)


@receiver(post_save, sender=LoteMateriaPrima)
def atualizar_status_lote_pos_criacao(sender, instance, created, **kwargs):
    """
    Atualiza o status do lote após criação ou modificação
    """
    if not created:  # Apenas para atualizações
        instance.atualizar_status()


# Signal para alertas de estoque baixo
@receiver(post_save, sender=MovimentacaoEstoque)
def verificar_estoque_baixo(sender, instance, created, **kwargs):
    """
    Verifica se o estoque atingiu nível baixo e cria alerta
    """
    if created and not instance.cancelada:
        mp = instance.materia_prima
        
        # Verificar se estoque está baixo
        if mp.status_estoque in ['baixo', 'zerado']:
            # Aqui você pode implementar sistema de notificações
            # Por exemplo: enviar email, criar notificação no sistema, etc.
            
            import logging
            logger = logging.getLogger('apps.estoque')
            
            logger.warning(
                f"ALERTA: Estoque baixo - {mp.descricao} - "
                f"Estoque atual: {mp.quantidade_em_estoque} {mp.unidade} - "
                f"Mínimo: {mp.estoque_minimo} {mp.unidade}"
            )


# Signal para alertas de lotes próximos ao vencimento
@receiver(post_save, sender=LoteMateriaPrima)
def verificar_lotes_proximo_vencimento(sender, instance, created, **kwargs):
    """
    Verifica lotes próximos ao vencimento
    """
    if instance.data_validade and instance.esta_proximo_vencimento:
        import logging
        logger = logging.getLogger('apps.estoque')
        
        logger.warning(
            f"ALERTA: Lote próximo ao vencimento - "
            f"{instance.materia_prima.descricao} - "
            f"Lote: {instance.numero_lote} - "
            f"Vencimento: {instance.data_validade} - "
            f"Dias restantes: {instance.dias_para_vencimento}"
        ) 


@receiver([post_save, post_delete], sender=MovimentacaoEstoque)
def atualizar_estoque_materia_prima(sender, instance, **kwargs):
    """
    Atualiza o campo quantidade_atual da matéria-prima sempre que uma
    movimentação é criada, alterada ou deletada.
    """
    materia_prima = instance.materia_prima

    # Usamos aggregate para calcular a soma total de forma eficiente no banco.
    # O valor de retorno pode ser None se não houver movimentações.
    resultado = materia_prima.movimentacoes.aggregate(
        total_estoque=Sum('quantidade')
    )

    novo_estoque = resultado['total_estoque'] or Decimal('0.0')

    # Atualizamos o campo usando update() para evitar recursão de signals
    # e ser mais performático, pois não chama o método .save() do modelo.
    MateriaPrima.objects.filter(pk=materia_prima.pk).update(
        quantidade_atual=novo_estoque
    )

    print(f"✅ Estoque da Matéria-Prima '{materia_prima}' atualizado para: {novo_estoque}") 