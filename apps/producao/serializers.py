from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    OrdemProducao, GradeProducao, Departamento, MateriaPrima, 
    ConsumoMateriaPrima, ProcessoProducao, CapacidadeProducao, 
    RelatorioFaturamento, StatusOP
)
from apps.cadastros.models import Cliente, Produto, Fornecedor
from apps.core.models import Empresa


class UserSerializer(serializers.ModelSerializer):
    """Serializer básico para usuários"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class ClienteSerializer(serializers.ModelSerializer):
    """Serializer básico para clientes"""
    class Meta:
        model = Cliente
        fields = ['id', 'nome', 'email', 'telefone']


class ProdutoSerializer(serializers.ModelSerializer):
    """Serializer básico para produtos"""
    nome = serializers.CharField(source='referencia', read_only=True)
    preco = serializers.DecimalField(source='preco_unitario', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Produto
        fields = ['id', 'nome', 'codigo', 'referencia', 'preco']


class FornecedorSerializer(serializers.ModelSerializer):
    """Serializer básico para fornecedores"""
    class Meta:
        model = Fornecedor
        fields = ['id', 'nome', 'email', 'telefone']


class DepartamentoSerializer(serializers.ModelSerializer):
    """Serializer para departamentos de produção"""
    
    class Meta:
        model = Departamento
        fields = [
            'id', 'nome', 'descricao', 'ordem', 'ativo',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def create(self, validated_data):
        # Adicionar empresa automaticamente baseada no usuário
        request = self.context.get('request')
        if request and hasattr(request, 'empresa_atual'):
            validated_data['empresa'] = request.empresa_atual
        return super().create(validated_data)


class MateriaPrimaSerializer(serializers.ModelSerializer):
    """Serializer para matérias primas"""
    fornecedor_nome = serializers.CharField(source='fornecedor.nome', read_only=True)
    status_estoque = serializers.ReadOnlyField()
    
    class Meta:
        model = MateriaPrima
        fields = [
            'id', 'codigo', 'nome', 'descricao', 'unidade_medida',
            'preco_unitario', 'estoque_atual', 'estoque_minimo',
            'fornecedor', 'fornecedor_nome', 'ativo', 'status_estoque',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'empresa_atual'):
            validated_data['empresa'] = request.empresa_atual
        return super().create(validated_data)


class GradeProducaoSerializer(serializers.ModelSerializer):
    """Serializer para grade de produção"""
    porcentagem_concluida = serializers.ReadOnlyField()
    
    class Meta:
        model = GradeProducao
        fields = [
            'id', 'tamanho', 'quantidade', 'quantidade_produzida',
            'porcentagem_concluida', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ConsumoMateriaPrimaSerializer(serializers.ModelSerializer):
    """Serializer para consumo de matéria prima"""
    materia_prima_nome = serializers.CharField(source='materia_prima.nome', read_only=True)
    departamento_nome = serializers.CharField(source='departamento.nome', read_only=True)
    custo_total = serializers.ReadOnlyField()
    porcentagem_utilizada = serializers.ReadOnlyField()
    
    class Meta:
        model = ConsumoMateriaPrima
        fields = [
            'id', 'materia_prima', 'materia_prima_nome', 'departamento', 
            'departamento_nome', 'quantidade_necessaria', 'quantidade_utilizada',
            'custo_unitario', 'custo_total', 'porcentagem_utilizada',
            'observacoes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ProcessoProducaoSerializer(serializers.ModelSerializer):
    """Serializer para processos de produção"""
    departamento_nome = serializers.CharField(source='departamento.nome', read_only=True)
    responsavel_nome = serializers.CharField(source='responsavel.get_full_name', read_only=True)
    status = serializers.ReadOnlyField()
    
    class Meta:
        model = ProcessoProducao
        fields = [
            'id', 'departamento', 'departamento_nome', 'data_inicio', 
            'data_conclusao', 'responsavel', 'responsavel_nome',
            'porcentagem_concluida', 'status', 'observacoes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class OrdemProducaoListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de OPs"""
    cliente_nome = serializers.CharField(source='cliente.nome', read_only=True)
    produto_nome = serializers.SerializerMethodField()
    
    def get_produto_nome(self, obj):
        if obj.produto:
            return f"{obj.produto.codigo} - {obj.produto.referencia}"
        return ""
    responsavel_nome = serializers.CharField(source='responsavel.get_full_name', read_only=True)
    
    # Campos calculados
    quantidade_total = serializers.ReadOnlyField()
    preco_total = serializers.ReadOnlyField()
    status_color = serializers.ReadOnlyField()
    prioridade_color = serializers.ReadOnlyField()
    dias_para_previsao = serializers.ReadOnlyField()
    status_prazo = serializers.ReadOnlyField()
    
    class Meta:
        model = OrdemProducao
        fields = [
            'id', 'numero_op', 'op_externa',
            'cliente', 'cliente_nome', 'produto', 'produto_nome',
            'data_entrada', 'data_previsao', 'data_inicio', 'data_conclusao',
            'preco_unitario', 'quantidade_total', 'preco_total',
            'status', 'status_color', 'prioridade', 'prioridade_color',
            'responsavel', 'responsavel_nome', 'porcentagem_concluida',
            'dias_para_previsao', 'status_prazo', 'created_at'
        ]


class OrdemProducaoDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para detalhes da OP"""
    cliente = ClienteSerializer(read_only=True)
    produto = ProdutoSerializer(read_only=True)
    responsavel = UserSerializer(read_only=True)
    
    # Relacionamentos aninhados
    itens_grade = GradeProducaoSerializer(many=True, read_only=True)
    materias_primas = ConsumoMateriaPrimaSerializer(many=True, read_only=True)
    processos = ProcessoProducaoSerializer(many=True, read_only=True)
    
    # Campos calculados
    quantidade_total = serializers.ReadOnlyField()
    preco_total = serializers.ReadOnlyField()
    status_color = serializers.ReadOnlyField()
    prioridade_color = serializers.ReadOnlyField()
    dias_para_previsao = serializers.ReadOnlyField()
    status_prazo = serializers.ReadOnlyField()
    
    class Meta:
        model = OrdemProducao
        fields = [
            'id', 'numero_op', 'op_externa',
            'cliente', 'produto', 'data_entrada', 'data_previsao', 
            'data_inicio', 'data_conclusao', 'preco_unitario', 'custo_material',
            'status', 'status_color', 'prioridade', 'prioridade_color',
            'responsavel', 'porcentagem_concluida', 'observacoes',
            'quantidade_total', 'preco_total', 'dias_para_previsao', 'status_prazo',
            'itens_grade', 'materias_primas', 'processos',
            'created_at', 'updated_at'
        ]


class OrdemProducaoCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para criação e edição de OPs"""
    itens_grade = GradeProducaoSerializer(many=True, required=False)
    materias_primas = ConsumoMateriaPrimaSerializer(many=True, required=False)
    
    class Meta:
        model = OrdemProducao
        fields = [
            'numero_op', 'op_externa',
            'cliente', 'produto', 'data_previsao',
            'preco_unitario', 'custo_material', 'prioridade',
            'responsavel', 'observacoes', 'itens_grade', 'materias_primas'
        ]
    
    def validate_numero_op(self, value):
        """Validar unicidade do número da OP"""
        request = self.context.get('request')
        empresa = getattr(request, 'empresa_atual', None)
        
        if empresa:
            queryset = OrdemProducao.objects.filter(
                empresa=empresa, 
                numero_op=value
            )
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                raise serializers.ValidationError(
                    "Já existe uma OP com este número."
                )
        return value
    
    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'empresa_atual'):
            validated_data['empresa'] = request.empresa_atual
        
        # Extrair dados aninhados
        itens_grade = validated_data.pop('itens_grade', [])
        materias_primas = validated_data.pop('materias_primas', [])
        
        # Criar OP
        ordem_producao = OrdemProducao.objects.create(**validated_data)
        
        # Criar grade de produção
        for item_data in itens_grade:
            GradeProducao.objects.create(
                ordem_producao=ordem_producao,
                **item_data
            )
        
        # Criar consumo de matéria prima
        for material_data in materias_primas:
            ConsumoMateriaPrima.objects.create(
                ordem_producao=ordem_producao,
                **material_data
            )
        
        return ordem_producao
    
    def update(self, instance, validated_data):
        # Extrair dados aninhados
        itens_grade = validated_data.pop('itens_grade', None)
        materias_primas = validated_data.pop('materias_primas', None)
        
        # Atualizar OP
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Atualizar grade (se fornecida)
        if itens_grade is not None:
            instance.itens_grade.all().delete()
            for item_data in itens_grade:
                GradeProducao.objects.create(
                    ordem_producao=instance,
                    **item_data
                )
        
        # Atualizar matérias primas (se fornecida)
        if materias_primas is not None:
            instance.materias_primas.all().delete()
            for material_data in materias_primas:
                ConsumoMateriaPrima.objects.create(
                    ordem_producao=instance,
                    **material_data
                )
        
        return instance


class CapacidadeProducaoSerializer(serializers.ModelSerializer):
    """Serializer para capacidade de produção"""
    empresa_nome = serializers.CharField(source='empresa.nome', read_only=True)
    
    class Meta:
        model = CapacidadeProducao
        fields = [
            'id', 'empresa', 'empresa_nome', 'capacidade_diaria', 
            'capacidade_mensal', 'data_atualizacao', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'data_atualizacao']


class RelatorioFaturamentoSerializer(serializers.ModelSerializer):
    """Serializer para relatórios de faturamento"""
    empresa_nome = serializers.CharField(source='empresa.nome', read_only=True)
    
    class Meta:
        model = RelatorioFaturamento
        fields = [
            'id', 'empresa', 'empresa_nome', 'mes', 'ano',
            'entradas', 'saidas', 'a_produzir',
            'valor_entradas', 'valor_saidas', 'valor_recebido', 'falta_receber',
            'data_geracao'
        ]
        read_only_fields = ['data_geracao']


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer para estatísticas do dashboard"""
    total_ops = serializers.IntegerField()
    ops_em_producao = serializers.IntegerField()
    ops_concluidas = serializers.IntegerField()
    ops_atrasadas = serializers.IntegerField()
    
    capacidade_diaria = serializers.IntegerField()
    utilizacao_capacidade = serializers.DecimalField(max_digits=5, decimal_places=2)
    
    valor_em_producao = serializers.DecimalField(max_digits=12, decimal_places=2)
    valor_concluido = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    materias_primas_baixo_estoque = serializers.IntegerField()
    
    # Dados para gráficos
    ops_por_status = serializers.DictField()
    producao_por_mes = serializers.ListField()
    departamentos_ocupacao = serializers.ListField()


class BulkUpdateStatusSerializer(serializers.Serializer):
    """Serializer para atualização em lote de status"""
    op_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True
    )
    status = serializers.ChoiceField(choices=StatusOP.choices)
    
    def validate_op_ids(self, value):
        if not value:
            raise serializers.ValidationError("Deve fornecer pelo menos uma OP.")
        return value


class BulkUpdateProgressSerializer(serializers.Serializer):
    """Serializer para atualização em lote de progresso"""
    updates = serializers.ListField(
        child=serializers.DictField(child=serializers.DecimalField(max_digits=5, decimal_places=2)),
        write_only=True
    )
    
    def validate_updates(self, value):
        for update in value:
            if 'op_id' not in update or 'porcentagem' not in update:
                raise serializers.ValidationError(
                    "Cada atualização deve conter 'op_id' e 'porcentagem'."
                )
            if not (0 <= update['porcentagem'] <= 100):
                raise serializers.ValidationError(
                    "Porcentagem deve estar entre 0 e 100."
                )
        return value 