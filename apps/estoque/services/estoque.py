from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from ..models import MateriaPrima, MovimentacaoEstoque, TipoMovimentacao


class EstoqueService:
    """Service principal para operações de estoque"""
    
    @staticmethod
    @transaction.atomic
    def registrar_movimentacao(
        empresa,
        materia_prima,
        tipo_movimento,
        quantidade,
        custo_unitario=Decimal('0.0'),
        usuario=None,
        origem=None,
        observacoes="",
        numero_documento="",
        lote=None,
        motivo_ajuste="",
        **kwargs
    ):
        """
        Registra uma movimentação de estoque e atualiza o custo médio.
        
        Args:
            empresa: Empresa proprietária
            materia_prima: MateriaPrima a ser movimentada
            tipo_movimento: Tipo da movimentação (TipoMovimentacao)
            quantidade: Quantidade (positiva para entradas, negativa para saídas)
            custo_unitario: Custo unitário da transação
            usuario: Usuário responsável
            origem: Objeto de origem (OP, NF, etc.)
            observacoes: Observações adicionais
            numero_documento: Número do documento (NF, etc.)
            lote: Lote da matéria-prima (se aplicável)
            motivo_ajuste: Motivo para ajustes manuais
            
        Returns:
            MovimentacaoEstoque: Instância da movimentação criada
        """
        
        # 1. Validações
        EstoqueService._validar_movimentacao(
            materia_prima, tipo_movimento, quantidade, lote
        )
        
        # 2. Normalizar quantidade baseada no tipo
        quantidade_normalizada = EstoqueService._normalizar_quantidade(
            tipo_movimento, quantidade
        )
        
        # 3. Validar estoque suficiente para saídas
        if quantidade_normalizada < 0:
            EstoqueService._validar_estoque_suficiente(
                materia_prima, abs(quantidade_normalizada)
            )
        
        # 4. Criar a movimentação
        movimentacao = MovimentacaoEstoque.objects.create(
            empresa=empresa,
            materia_prima=materia_prima,
            tipo_movimento=tipo_movimento,
            quantidade=quantidade_normalizada,
            custo_unitario=custo_unitario,
            usuario=usuario,
            origem=origem,
            observacoes=observacoes,
            numero_documento=numero_documento,
            lote=lote,
            motivo_ajuste=motivo_ajuste,
            **kwargs
        )
        
        # 5. Atualizar custo médio ponderado (apenas para entradas)
        if tipo_movimento in TipoMovimentacao.get_entradas():
            from .custo_medio import CustoMedioService
            CustoMedioService.recalcular_custo_medio(
                materia_prima, quantidade_normalizada, custo_unitario
            )
        
        # 6. Atualizar status do lote se aplicável
        if lote:
            lote.atualizar_status()
        
        return movimentacao
    
    @staticmethod
    def registrar_entrada_compra(materia_prima, quantidade, custo_unitario, **kwargs):
        """Registra entrada por compra"""
        return EstoqueService.registrar_movimentacao(
            materia_prima=materia_prima,
            tipo_movimento=TipoMovimentacao.ENTRADA_COMPRA,
            quantidade=quantidade,
            custo_unitario=custo_unitario,
            **kwargs
        )
    
    @staticmethod
    def registrar_saida_producao(materia_prima, quantidade, ordem_producao, **kwargs):
        """Registra saída para produção"""
        return EstoqueService.registrar_movimentacao(
            materia_prima=materia_prima,
            tipo_movimento=TipoMovimentacao.SAIDA_PRODUCAO,
            quantidade=quantidade,
            origem=ordem_producao,
            **kwargs
        )
    
    @staticmethod
    def registrar_ajuste_entrada(materia_prima, quantidade, motivo, **kwargs):
        """Registra ajuste de entrada"""
        return EstoqueService.registrar_movimentacao(
            materia_prima=materia_prima,
            tipo_movimento=TipoMovimentacao.ENTRADA_AJUSTE,
            quantidade=quantidade,
            motivo_ajuste=motivo,
            **kwargs
        )
    
    @staticmethod
    def registrar_ajuste_saida(materia_prima, quantidade, motivo, **kwargs):
        """Registra ajuste de saída"""
        return EstoqueService.registrar_movimentacao(
            materia_prima=materia_prima,
            tipo_movimento=TipoMovimentacao.SAIDA_AJUSTE,
            quantidade=quantidade,
            motivo_ajuste=motivo,
            **kwargs
        )
    
    @staticmethod
    def verificar_disponibilidade(materia_prima, quantidade_necessaria):
        """
        Verifica se há estoque suficiente
        
        Returns:
            dict: {
                'disponivel': bool,
                'estoque_atual': Decimal,
                'quantidade_necessaria': Decimal,
                'diferenca': Decimal
            }
        """
        estoque_atual = materia_prima.quantidade_em_estoque
        disponivel = estoque_atual >= quantidade_necessaria
        diferenca = estoque_atual - quantidade_necessaria
        
        return {
            'disponivel': disponivel,
            'estoque_atual': estoque_atual,
            'quantidade_necessaria': quantidade_necessaria,
            'diferenca': diferenca
        }
    
    @staticmethod
    def calcular_valor_total_estoque(empresa, categoria=None):
        """Calcula valor total do estoque"""
        materias = MateriaPrima.objects.filter(empresa=empresa, ativo=True)
        
        if categoria:
            materias = materias.filter(categoria=categoria)
        
        valor_total = sum(mp.valor_total_em_estoque for mp in materias)
        return valor_total
    
    @staticmethod
    def listar_materias_estoque_baixo(empresa):
        """Lista matérias-primas com estoque baixo"""
        materias = MateriaPrima.objects.filter(empresa=empresa, ativo=True)
        estoque_baixo = []
        
        for mp in materias:
            if mp.status_estoque in ['zerado', 'baixo']:
                estoque_baixo.append(mp)
        
        return estoque_baixo
    
    @staticmethod
    def listar_materias_sem_movimento(empresa, dias=30):
        """Lista matérias-primas sem movimento há X dias"""
        from datetime import timedelta
        data_limite = timezone.now() - timedelta(days=dias)
        
        materias = MateriaPrima.objects.filter(empresa=empresa, ativo=True)
        sem_movimento = []
        
        for mp in materias:
            ultima_movimentacao = mp.movimentacoes.first()
            if not ultima_movimentacao or ultima_movimentacao.data_movimento < data_limite:
                sem_movimento.append(mp)
        
        return sem_movimento
    
    # --- Métodos Privados ---
    
    @staticmethod
    def _validar_movimentacao(materia_prima, tipo_movimento, quantidade, lote):
        """Validações da movimentação"""
        if quantidade == 0:
            raise ValueError("Quantidade não pode ser zero")
        
        if not materia_prima.ativo:
            raise ValueError("Matéria-prima está inativa")
        
        # Validar lote se necessário
        if materia_prima.controlar_lote and not lote:
            if tipo_movimento in TipoMovimentacao.get_saidas():
                raise ValueError("Lote é obrigatório para esta matéria-prima")
        
        if lote and lote.materia_prima != materia_prima:
            raise ValueError("Lote não pertence a esta matéria-prima")
    
    @staticmethod
    def _normalizar_quantidade(tipo_movimento, quantidade):
        """Normaliza a quantidade baseada no tipo de movimento"""
        if tipo_movimento in TipoMovimentacao.get_entradas():
            return abs(quantidade)  # Entradas sempre positivas
        elif tipo_movimento in TipoMovimentacao.get_saidas():
            return -abs(quantidade)  # Saídas sempre negativas
        else:
            return quantidade  # Manter como está
    
    @staticmethod
    def _validar_estoque_suficiente(materia_prima, quantidade_saida):
        """Valida se há estoque suficiente para saída"""
        estoque_atual = materia_prima.quantidade_em_estoque
        
        if estoque_atual < quantidade_saida:
            raise ValueError(
                f"Estoque insuficiente. "
                f"Disponível: {estoque_atual} {materia_prima.unidade}, "
                f"Necessário: {quantidade_saida} {materia_prima.unidade}"
            ) 