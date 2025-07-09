# from django.dispatch import receiver
# from django.utils import timezone
# from apps.producao.signals import op_concluida
# from .models import ContaReceber


# @receiver(op_concluida)
# def criar_conta_receber_apos_op(sender, ordem_producao, **kwargs):
#     """
#     Escuta o sinal de que uma OP foi concluída e cria a conta a receber.
#     Temporariamente desativado após a simplificação do app producao.
#     """
#     # Verificar se já existe conta para esta OP para evitar duplicatas
#     conta_existente = ContaReceber.objects.filter(
#         ordem_producao=ordem_producao
#     ).exists()

#     if not conta_existente:
#         # Calcular data de vencimento (ex: 30 dias após conclusão)
#         data_vencimento = timezone.now().date() + timezone.timedelta(days=30)
        
#         # O campo 'produto' na OP pode ser nulo, então tratamos isso
#         descricao_produto = "Produto"
#         if ordem_producao.produto and hasattr(ordem_producao.produto, 'referencia'):
#             descricao_produto = ordem_producao.produto.referencia

#         ContaReceber.objects.create(
#             empresa=ordem_producao.empresa,
#             ordem_producao=ordem_producao,
#             cliente=ordem_producao.cliente,
#             descricao=f"Produção OP {ordem_producao.numero_op} - {descricao_produto}",
#             valor_total=ordem_producao.preco_total,
#             data_emissao=timezone.now().date(),
#             data_vencimento=data_vencimento,
#             status='PENDENTE'
#         )
        
#         print(f"✅ [SINAL RECEBIDO] Conta a receber criada automaticamente para OP {ordem_producao.numero_op}")

#     else:
#         print(f"ℹ️ [SINAL RECEBIDO] Conta a receber para OP {ordem_producao.numero_op} já existe. Nenhuma ação foi tomada.") 