from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from .models import OrdemProducao, StatusOP
from apps.financeiro.models import ContaReceber, StatusPagamento


@receiver(pre_save, sender=OrdemProducao)
def verificar_mudanca_status(sender, instance, **kwargs):
    """
    Signal para capturar mudanças no status da OP
    e criar conta a receber automaticamente quando finalizada
    """
    # Verificar se é uma atualização (não criação)
    if instance.pk:
        try:
            # Buscar o estado anterior da OP
            op_anterior = OrdemProducao.objects.get(pk=instance.pk)
            
            # Verificar se houve mudança para CONCLUIDA
            if (op_anterior.status != StatusOP.CONCLUIDA and 
                instance.status == StatusOP.CONCLUIDA):
                
                # Marcar para criar conta a receber após o save
                instance._criar_conta_receber = True
                
                # Definir data de conclusão se não estiver definida
                if not instance.data_conclusao:
                    instance.data_conclusao = timezone.now().date()
                    
        except OrdemProducao.DoesNotExist:
            # OP não existe ainda (primeira criação)
            pass


@receiver(post_save, sender=OrdemProducao)
def criar_conta_receber_automatica(sender, instance, created, **kwargs):
    """
    Signal executado após salvar OP
    Cria conta a receber automaticamente quando OP é finalizada
    """
    # Verificar se deve criar conta a receber
    if hasattr(instance, '_criar_conta_receber') and instance._criar_conta_receber:
        
        # Verificar se já existe conta para esta OP
        if not ContaReceber.objects.filter(ordem_producao=instance).exists():
            
            # Calcular data de vencimento (30 dias após conclusão por padrão)
            data_vencimento = instance.data_conclusao + timedelta(days=30)
            
            # Criar a conta a receber
            conta = ContaReceber.objects.create(
                empresa=instance.empresa,
                ordem_producao=instance,
                cliente=instance.cliente,
                descricao=f"Faturamento OP {instance.numero_op} - {instance.produto.referencia if instance.produto else 'Produto'}",
                valor_total=instance.preco_total,
                data_emissao=instance.data_conclusao,
                data_vencimento=data_vencimento,
                status=StatusPagamento.PENDENTE,
                observacoes=f"Conta gerada automaticamente pela finalização da OP {instance.numero_op}"
            )
            
            # Log da criação (opcional - para debug)
            print(f"✅ Conta a receber {conta.numero_conta} criada automaticamente para OP {instance.numero_op}")
        
        # Remover a flag
        delattr(instance, '_criar_conta_receber')


@receiver(post_save, sender=OrdemProducao)
def atualizar_faturamento_mensal(sender, instance, created, **kwargs):
    """
    Signal para atualizar automaticamente o faturamento mensal
    quando uma OP for criada ou concluída
    """
    from apps.financeiro.models import FaturamentoMensal
    
    # Atualizar faturamento do mês atual
    hoje = timezone.now().date()
    FaturamentoMensal.atualizar_faturamento(
        empresa=instance.empresa,
        mes=hoje.month,
        ano=hoje.year
    )
    
    # Se OP foi concluída, também atualizar o mês de conclusão (se diferente)
    if instance.status == StatusOP.CONCLUIDA and instance.data_conclusao:
        if (instance.data_conclusao.month != hoje.month or 
            instance.data_conclusao.year != hoje.year):
            
            FaturamentoMensal.atualizar_faturamento(
                empresa=instance.empresa,
                mes=instance.data_conclusao.month,
                ano=instance.data_conclusao.year
            ) 