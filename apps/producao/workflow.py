"""
Sistema de Workflow para Ordens de Produção
Gerencia as transições de status e etapas da produção
"""

from django.db import transaction
from django.utils import timezone
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)


class WorkflowOP:
    """
    Classe principal para gerenciar o workflow das OPs
    """
    
    # Definir o fluxo de status permitidos
    TRANSICOES_PERMITIDAS = {
        "CADASTRADA": ["PREPARACAO", "CANCELADA"],
        "PREPARACAO": ["FRENTE_EXTERNA", "CADASTRADA", "CANCELADA"],
        "FRENTE_EXTERNA": ["MONTAGEM", "PREPARACAO", "CANCELADA"],
        "MONTAGEM": ["EM_PRODUCAO", "FRENTE_EXTERNA", "CANCELADA"],
        "EM_PRODUCAO": ["CONCLUIDA", "MONTAGEM", "CANCELADA"],
        "CONCLUIDA": ["FINALIZADA", "EM_PRODUCAO"],
        "FINALIZADA": ["ENTREGUE", "CONCLUIDA"],
        "ENTREGUE": [],  # Status final
        "CANCELADA": ["CADASTRADA"],  # Permite reativar
    }
    
    def __init__(self, ordem_producao):
        self.op = ordem_producao
    
    def pode_transicionar_para(self, novo_status):
        """Verifica se a OP pode transicionar para o novo status"""
        status_atual = self.op.status
        return novo_status in self.TRANSICOES_PERMITIDAS.get(status_atual, [])
    
    def transicionar_para(self, novo_status, usuario=None, observacoes=""):
        """
        Executa a transição de status da OP
        """
        if not self.pode_transicionar_para(novo_status):
            raise ValueError(f"Transição de {self.op.status} para {novo_status} não é permitida")
        
        with transaction.atomic():
            status_anterior = self.op.status
            self.op.status = novo_status
            
            # Atualizar datas baseadas no status
            agora = timezone.now()
            
            if novo_status == "PREPARACAO" and not self.op.data_inicio:
                self.op.data_inicio = agora.date()
            elif novo_status == "CONCLUIDA" and not self.op.data_conclusao:
                self.op.data_conclusao = agora.date()
                self.op.porcentagem_concluida = 100
            
            self.op.save()
            
            logger.info(f"OP {self.op.numero_op} transicionou de {status_anterior} para {novo_status}")
    
    @classmethod
    def obter_proximos_status(cls, status_atual):
        """Retorna lista de próximos status possíveis"""
        return cls.TRANSICOES_PERMITIDAS.get(status_atual, [])


def avancar_op(op_id, usuario=None):
    """Avança OP para próximo status"""
    from .models import OrdemProducao
    op = OrdemProducao.objects.get(id=op_id)
    workflow = WorkflowOP(op)
    proximos = workflow.obter_proximos_status(op.status)
    if proximos and proximos[0] != "CANCELADA":
        workflow.transicionar_para(proximos[0], usuario)
        return True
    return False

