from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from ..models import InventarioFisico, ItemInventario, MateriaPrima, StatusInventario


class InventarioService:
    """Service para gestão de inventários físicos"""
    
    @staticmethod
    @transaction.atomic
    def criar_inventario(
        empresa, 
        descricao, 
        responsavel, 
        categoria_filtro=None, 
        incluir_zerados=False
    ):
        """
        Cria um novo inventário físico
        
        Args:
            empresa: Empresa proprietária
            descricao: Descrição do inventário
            responsavel: Usuário responsável
            categoria_filtro: Categoria para filtrar (opcional)
            incluir_zerados: Se deve incluir itens com estoque zero
            
        Returns:
            InventarioFisico: Inventário criado
        """
        
        # Gerar número sequencial
        numero = InventarioService._gerar_numero_inventario(empresa)
        
        # Criar inventário
        inventario = InventarioFisico.objects.create(
            empresa=empresa,
            numero=numero,
            descricao=descricao,
            responsavel=responsavel,
            categoria_filtro=categoria_filtro,
            incluir_zerados=incluir_zerados
        )
        
        # Gerar itens automaticamente
        inventario.gerar_itens()
        
        return inventario
    
    @staticmethod
    @transaction.atomic
    def iniciar_inventario(inventario):
        """
        Inicia um inventário (muda status para EM_ANDAMENTO)
        
        Args:
            inventario: InventarioFisico a ser iniciado
        """
        if inventario.status != StatusInventario.ABERTO:
            raise ValueError("Inventário deve estar ABERTO para ser iniciado")
        
        inventario.status = StatusInventario.EM_ANDAMENTO
        inventario.data_inicio = timezone.now()
        inventario.save()
    
    @staticmethod
    @transaction.atomic
    def registrar_contagem(item_inventario, quantidade_fisica, usuario, observacoes=""):
        """
        Registra a contagem física de um item
        
        Args:
            item_inventario: ItemInventario a ser contado
            quantidade_fisica: Quantidade contada fisicamente
            usuario: Usuário que fez a contagem
            observacoes: Observações da contagem
        """
        if item_inventario.inventario.status != StatusInventario.EM_ANDAMENTO:
            raise ValueError("Inventário deve estar EM_ANDAMENTO para registrar contagens")
        
        item_inventario.marcar_como_contado(quantidade_fisica, usuario)
        if observacoes:
            item_inventario.observacoes = observacoes
            item_inventario.save()
    
    @staticmethod
    @transaction.atomic
    def finalizar_inventario(inventario, gerar_ajustes=True, usuario=None):
        """
        Finaliza um inventário e gera ajustes se necessário
        
        Args:
            inventario: InventarioFisico a ser finalizado
            gerar_ajustes: Se deve gerar movimentações de ajuste
            usuario: Usuário responsável pela finalização
            
        Returns:
            dict: Resumo dos ajustes gerados
        """
        if inventario.status != StatusInventario.EM_ANDAMENTO:
            raise ValueError("Inventário deve estar EM_ANDAMENTO para ser finalizado")
        
        # Verificar se todos os itens foram contados
        itens_pendentes = inventario.itens.filter(contado=False)
        if itens_pendentes.exists():
            raise ValueError(f"Ainda há {itens_pendentes.count()} itens não contados")
        
        # Finalizar inventário
        inventario.status = StatusInventario.FINALIZADO
        inventario.data_finalizacao = timezone.now()
        inventario.save()
        
        resumo_ajustes = {
            'total_ajustes': 0,
            'entradas_geradas': 0,
            'saidas_geradas': 0,
            'valor_total_ajustes': Decimal('0.00'),
            'itens_ajustados': []
        }
        
        # Gerar ajustes se solicitado
        if gerar_ajustes:
            from .estoque import EstoqueService
            from ..models import TipoMovimentacao
            
            for item in inventario.itens.exclude(diferenca=0):
                try:
                    if item.diferenca > 0:
                        # Entrada por inventário
                        movimentacao = EstoqueService.registrar_movimentacao(
                            empresa=inventario.empresa,
                            materia_prima=item.materia_prima,
                            tipo_movimento=TipoMovimentacao.ENTRADA_INVENTARIO,
                            quantidade=item.diferenca,
                            custo_unitario=item.custo_unitario,
                            usuario=usuario,
                            origem=inventario,
                            observacoes=f"Ajuste por inventário {inventario.numero}",
                            motivo_ajuste=f"Inventário físico - sobra de {item.diferenca}"
                        )
                        resumo_ajustes['entradas_geradas'] += 1
                    else:
                        # Saída por inventário
                        movimentacao = EstoqueService.registrar_movimentacao(
                            empresa=inventario.empresa,
                            materia_prima=item.materia_prima,
                            tipo_movimento=TipoMovimentacao.SAIDA_INVENTARIO,
                            quantidade=item.diferenca,
                            custo_unitario=item.custo_unitario,
                            usuario=usuario,
                            origem=inventario,
                            observacoes=f"Ajuste por inventário {inventario.numero}",
                            motivo_ajuste=f"Inventário físico - falta de {abs(item.diferenca)}"
                        )
                        resumo_ajustes['saidas_geradas'] += 1
                    
                    # Adicionar ao resumo
                    resumo_ajustes['total_ajustes'] += 1
                    resumo_ajustes['valor_total_ajustes'] += item.valor_diferenca
                    resumo_ajustes['itens_ajustados'].append({
                        'materia_prima': item.materia_prima.descricao,
                        'diferenca': item.diferenca,
                        'valor_diferenca': item.valor_diferenca,
                        'tipo': 'entrada' if item.diferenca > 0 else 'saida'
                    })
                    
                except Exception as e:
                    # Log do erro mas não falha o processo todo
                    print(f"Erro ao gerar ajuste para {item.materia_prima.descricao}: {e}")
        
        return resumo_ajustes
    
    @staticmethod
    def cancelar_inventario(inventario, motivo=""):
        """
        Cancela um inventário
        
        Args:
            inventario: InventarioFisico a ser cancelado
            motivo: Motivo do cancelamento
        """
        if inventario.status == StatusInventario.FINALIZADO:
            raise ValueError("Não é possível cancelar um inventário finalizado")
        
        inventario.status = StatusInventario.CANCELADO
        inventario.observacoes += f"\n\nCANCELADO: {motivo}"
        inventario.save()
    
    @staticmethod
    def obter_relatorio_inventario(inventario):
        """
        Gera relatório completo do inventário
        
        Args:
            inventario: InventarioFisico para gerar relatório
            
        Returns:
            dict: Relatório completo
        """
        itens = inventario.itens.all()
        
        # Estatísticas gerais
        total_itens = itens.count()
        itens_contados = itens.filter(contado=True).count()
        itens_com_diferenca = itens.exclude(diferenca=0).count()
        
        # Valores
        valor_sistema = sum(item.quantidade_sistema * item.custo_unitario for item in itens)
        valor_fisico = sum(item.quantidade_fisica * item.custo_unitario for item in itens if item.contado)
        valor_diferenca = sum(item.valor_diferenca for item in itens if item.contado)
        
        # Diferenças por tipo
        sobras = itens.filter(diferenca__gt=0)
        faltas = itens.filter(diferenca__lt=0)
        
        valor_sobras = sum(item.valor_diferenca for item in sobras)
        valor_faltas = sum(abs(item.valor_diferenca) for item in faltas)
        
        return {
            'inventario': inventario,
            'estatisticas': {
                'total_itens': total_itens,
                'itens_contados': itens_contados,
                'itens_pendentes': total_itens - itens_contados,
                'percentual_conclusao': (itens_contados / total_itens * 100) if total_itens > 0 else 0,
                'itens_com_diferenca': itens_com_diferenca,
                'percentual_diferencas': (itens_com_diferenca / itens_contados * 100) if itens_contados > 0 else 0
            },
            'valores': {
                'valor_sistema': valor_sistema,
                'valor_fisico': valor_fisico,
                'valor_diferenca': valor_diferenca,
                'valor_sobras': valor_sobras,
                'valor_faltas': valor_faltas
            },
            'diferencas': {
                'total_sobras': sobras.count(),
                'total_faltas': faltas.count(),
                'valor_sobras': valor_sobras,
                'valor_faltas': valor_faltas
            }
        }
    
    @staticmethod
    def listar_inventarios_pendentes(empresa):
        """Lista inventários em andamento"""
        return InventarioFisico.objects.filter(
            empresa=empresa,
            status__in=[StatusInventario.ABERTO, StatusInventario.EM_ANDAMENTO]
        ).order_by('-data_abertura')
    
    @staticmethod
    def obter_historico_inventarios(empresa, limite=10):
        """Obtém histórico de inventários finalizados"""
        return InventarioFisico.objects.filter(
            empresa=empresa,
            status=StatusInventario.FINALIZADO
        ).order_by('-data_finalizacao')[:limite]
    
    # --- Métodos Privados ---
    
    @staticmethod
    def _gerar_numero_inventario(empresa):
        """Gera número sequencial para o inventário"""
        hoje = timezone.now().date()
        ano_mes = hoje.strftime('%Y%m')
        
        # Contar inventários do mês
        count = InventarioFisico.objects.filter(
            empresa=empresa,
            data_abertura__year=hoje.year,
            data_abertura__month=hoje.month
        ).count()
        
        return f"INV{ano_mes}{count + 1:03d}" 