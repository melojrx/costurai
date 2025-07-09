from decimal import Decimal
from django.db import transaction
from ..models import MateriaPrima, MovimentacaoEstoque, TipoMovimentacao


class CustoMedioService:
    """Service para cálculo e gestão do custo médio ponderado"""
    
    @staticmethod
    @transaction.atomic
    def recalcular_custo_medio(materia_prima, nova_entrada_qtd, novo_custo_unitario):
        """
        Recalcula o custo médio ponderado após uma entrada
        
        Fórmula: CMP = (Valor_Estoque_Anterior + Valor_Nova_Entrada) / (Qtd_Anterior + Qtd_Nova)
        
        Args:
            materia_prima: MateriaPrima a ser atualizada
            nova_entrada_qtd: Quantidade da nova entrada (positiva)
            novo_custo_unitario: Custo unitário da nova entrada
            
        Returns:
            Decimal: Novo custo médio ponderado
        """
        
        # Obter estoque anterior (antes desta entrada)
        estoque_anterior = materia_prima.quantidade_em_estoque - nova_entrada_qtd
        
        # Calcular valor do estoque anterior
        valor_estoque_anterior = estoque_anterior * materia_prima.custo_medio_ponderado
        
        # Calcular valor da nova entrada
        valor_nova_entrada = nova_entrada_qtd * novo_custo_unitario
        
        # Calcular novo estoque total e valor total
        novo_estoque_total = estoque_anterior + nova_entrada_qtd
        novo_valor_total = valor_estoque_anterior + valor_nova_entrada
        
        # Calcular novo custo médio
        if novo_estoque_total > 0:
            novo_custo_medio = novo_valor_total / novo_estoque_total
        else:
            # Se estoque for zero, usar o custo da entrada
            novo_custo_medio = novo_custo_unitario
        
        # Atualizar matéria-prima
        materia_prima.custo_medio_ponderado = novo_custo_medio
        materia_prima.custo_ultima_compra = novo_custo_unitario
        materia_prima.save(update_fields=[
            'custo_medio_ponderado', 
            'custo_ultima_compra'
        ])
        
        return novo_custo_medio
    
    @staticmethod
    @transaction.atomic
    def recalcular_custo_medio_completo(materia_prima):
        """
        Recalcula o custo médio baseado em todo o histórico de movimentações.
        Útil para correções ou após cancelamento de movimentações.
        
        Args:
            materia_prima: MateriaPrima a ser recalculada
            
        Returns:
            Decimal: Novo custo médio ponderado
        """
        
        # Obter todas as entradas não canceladas em ordem cronológica
        entradas = MovimentacaoEstoque.objects.filter(
            materia_prima=materia_prima,
            tipo_movimento__in=TipoMovimentacao.get_entradas(),
            cancelada=False
        ).order_by('data_movimento')
        
        if not entradas.exists():
            # Se não há entradas, zerar o custo
            materia_prima.custo_medio_ponderado = Decimal('0.0000')
            materia_prima.save(update_fields=['custo_medio_ponderado'])
            return Decimal('0.0000')
        
        # Simular o cálculo entrada por entrada
        estoque_acumulado = Decimal('0.000')
        valor_acumulado = Decimal('0.0000')
        
        for entrada in entradas:
            quantidade_entrada = abs(entrada.quantidade)
            custo_entrada = entrada.custo_unitario
            
            # Calcular novo total
            novo_estoque = estoque_acumulado + quantidade_entrada
            novo_valor = valor_acumulado + (quantidade_entrada * custo_entrada)
            
            # Atualizar acumuladores
            estoque_acumulado = novo_estoque
            valor_acumulado = novo_valor
        
        # Calcular custo médio final
        if estoque_acumulado > 0:
            custo_medio_final = valor_acumulado / estoque_acumulado
        else:
            custo_medio_final = Decimal('0.0000')
        
        # Atualizar matéria-prima
        materia_prima.custo_medio_ponderado = custo_medio_final
        
        # Atualizar custo da última compra
        ultima_compra = entradas.filter(
            tipo_movimento=TipoMovimentacao.ENTRADA_COMPRA
        ).last()
        if ultima_compra:
            materia_prima.custo_ultima_compra = ultima_compra.custo_unitario
        
        materia_prima.save(update_fields=[
            'custo_medio_ponderado', 
            'custo_ultima_compra'
        ])
        
        return custo_medio_final
    
    @staticmethod
    def simular_custo_medio(materia_prima, quantidade_entrada, custo_entrada):
        """
        Simula qual seria o novo custo médio após uma entrada
        (sem salvar no banco)
        
        Args:
            materia_prima: MateriaPrima para simulação
            quantidade_entrada: Quantidade da entrada simulada
            custo_entrada: Custo unitário da entrada simulada
            
        Returns:
            dict: {
                'custo_atual': Decimal,
                'custo_simulado': Decimal,
                'diferenca': Decimal,
                'percentual_variacao': Decimal
            }
        """
        
        custo_atual = materia_prima.custo_medio_ponderado
        estoque_atual = materia_prima.quantidade_em_estoque
        
        # Calcular custo simulado
        valor_estoque_atual = estoque_atual * custo_atual
        valor_entrada = quantidade_entrada * custo_entrada
        
        novo_estoque = estoque_atual + quantidade_entrada
        novo_valor = valor_estoque_atual + valor_entrada
        
        if novo_estoque > 0:
            custo_simulado = novo_valor / novo_estoque
        else:
            custo_simulado = custo_entrada
        
        # Calcular diferenças
        diferenca = custo_simulado - custo_atual
        
        if custo_atual > 0:
            percentual_variacao = (diferenca / custo_atual) * 100
        else:
            percentual_variacao = Decimal('0.00')
        
        return {
            'custo_atual': custo_atual,
            'custo_simulado': custo_simulado,
            'diferenca': diferenca,
            'percentual_variacao': percentual_variacao
        }
    
    @staticmethod
    def obter_historico_custos(materia_prima, limite=50):
        """
        Obtém o histórico de custos baseado nas entradas
        
        Args:
            materia_prima: MateriaPrima para análise
            limite: Número máximo de registros
            
        Returns:
            list: Lista com histórico de custos
        """
        
        entradas = MovimentacaoEstoque.objects.filter(
            materia_prima=materia_prima,
            tipo_movimento__in=TipoMovimentacao.get_entradas(),
            cancelada=False
        ).order_by('-data_movimento')[:limite]
        
        historico = []
        for entrada in entradas:
            historico.append({
                'data': entrada.data_movimento,
                'tipo': entrada.get_tipo_movimento_display(),
                'quantidade': entrada.quantidade,
                'custo_unitario': entrada.custo_unitario,
                'valor_total': entrada.valor_total,
                'documento': entrada.numero_documento,
                'fornecedor': entrada.origem if hasattr(entrada.origem, 'nome') else None
            })
        
        return historico
    
    @staticmethod
    def analisar_variacao_custos(materia_prima, dias=90):
        """
        Analisa a variação de custos nos últimos dias
        
        Args:
            materia_prima: MateriaPrima para análise
            dias: Período de análise em dias
            
        Returns:
            dict: Análise da variação de custos
        """
        from django.utils import timezone
        from datetime import timedelta
        
        data_limite = timezone.now() - timedelta(days=dias)
        
        entradas = MovimentacaoEstoque.objects.filter(
            materia_prima=materia_prima,
            tipo_movimento=TipoMovimentacao.ENTRADA_COMPRA,
            data_movimento__gte=data_limite,
            cancelada=False
        ).order_by('data_movimento')
        
        if not entradas.exists():
            return {
                'periodo_dias': dias,
                'total_entradas': 0,
                'custo_minimo': None,
                'custo_maximo': None,
                'custo_medio': None,
                'variacao_percentual': None,
                'tendencia': 'estavel'
            }
        
        custos = [e.custo_unitario for e in entradas]
        custo_minimo = min(custos)
        custo_maximo = max(custos)
        custo_medio = sum(custos) / len(custos)
        
        # Calcular variação percentual
        if custo_minimo > 0:
            variacao_percentual = ((custo_maximo - custo_minimo) / custo_minimo) * 100
        else:
            variacao_percentual = Decimal('0.00')
        
        # Determinar tendência (comparar primeiro e último)
        primeiro_custo = custos[0]
        ultimo_custo = custos[-1]
        
        if ultimo_custo > primeiro_custo * Decimal('1.05'):  # +5%
            tendencia = 'alta'
        elif ultimo_custo < primeiro_custo * Decimal('0.95'):  # -5%
            tendencia = 'baixa'
        else:
            tendencia = 'estavel'
        
        return {
            'periodo_dias': dias,
            'total_entradas': len(custos),
            'custo_minimo': custo_minimo,
            'custo_maximo': custo_maximo,
            'custo_medio': custo_medio,
            'variacao_percentual': variacao_percentual,
            'tendencia': tendencia,
            'primeiro_custo': primeiro_custo,
            'ultimo_custo': ultimo_custo
        } 