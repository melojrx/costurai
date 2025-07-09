from django import forms
from django.core.exceptions import ValidationError
from .models import MateriaPrima, MovimentacaoEstoque, TipoMovimentacao, CategoriaMateriaPrima


class MateriaPrimaForm(forms.ModelForm):
    """Form para criar/editar matérias-primas"""
    
    class Meta:
        model = MateriaPrima
        fields = [
            'codigo', 'codigo_barras', 'descricao', 'categoria',
            'unidade', 'fornecedor_preferencial', 'estoque_minimo',
            'estoque_maximo', 'controlar_lote', 'tem_validade',
            'observacoes', 'ativo'
        ]
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: MP001'
            }),
            'codigo_barras': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Código de barras (opcional)'
            }),
            'descricao': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Descrição da matéria-prima'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-control'
            }),
            'unidade': forms.Select(attrs={
                'class': 'form-control'
            }),
            'fornecedor_preferencial': forms.Select(attrs={
                'class': 'form-control'
            }),
            'estoque_minimo': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.001'
            }),
            'estoque_maximo': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.001'
            }),
            'controlar_lote': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'tem_validade': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'ativo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        
        if empresa:
            # Filtrar categorias por empresa
            self.fields['categoria'].queryset = CategoriaMateriaPrima.objects.filter(
                empresa=empresa, ativo=True
            )
            
            # Filtrar fornecedores por empresa
            try:
                from apps.cadastros.models import Fornecedor
                self.fields['fornecedor_preferencial'].queryset = Fornecedor.objects.filter(
                    empresa=empresa, ativo=True
                )
            except ImportError:
                pass

    def clean_codigo(self):
        """Validar código único por empresa"""
        codigo = self.cleaned_data.get('codigo')
        if codigo:
            # Verificar se já existe outro registro com mesmo código
            qs = MateriaPrima.objects.filter(codigo=codigo)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise ValidationError("Já existe uma matéria-prima com este código.")
        
        return codigo

    def clean(self):
        """Validações gerais"""
        cleaned_data = super().clean()
        estoque_minimo = cleaned_data.get('estoque_minimo')
        estoque_maximo = cleaned_data.get('estoque_maximo')
        
        # Validar estoque mínimo vs máximo
        if estoque_minimo and estoque_maximo:
            if estoque_minimo > estoque_maximo:
                raise ValidationError({
                    'estoque_minimo': 'Estoque mínimo não pode ser maior que o máximo.'
                })
        
        return cleaned_data


class CategoriaMateriaPrimaForm(forms.ModelForm):
    """Form para criar/editar categorias de matérias-primas"""
    
    class Meta:
        model = CategoriaMateriaPrima
        fields = ['nome', 'descricao', 'cor_hex', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome da categoria'
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Descrição da categoria (opcional)'
            }),
            'cor_hex': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color',
                'value': '#3b82f6'
            }),
            'ativo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def clean_nome(self):
        """Validar nome único por empresa"""
        nome = self.cleaned_data.get('nome')
        if nome:
            # Verificar se já existe outro registro com mesmo nome
            qs = CategoriaMateriaPrima.objects.filter(nome=nome)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            
            if qs.exists():
                raise ValidationError("Já existe uma categoria com este nome.")
        
        return nome


class MovimentacaoEstoqueForm(forms.ModelForm):
    """Form para registrar movimentações de estoque"""
    
    class Meta:
        model = MovimentacaoEstoque
        fields = [
            'materia_prima', 'tipo_movimento', 'quantidade',
            'custo_unitario', 'numero_documento', 'observacoes'
        ]
        widgets = {
            'materia_prima': forms.Select(attrs={
                'class': 'form-control'
            }),
            'tipo_movimento': forms.Select(attrs={
                'class': 'form-control'
            }),
            'quantidade': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001',
                'min': '0.001'
            }),
            'custo_unitario': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0001',
                'min': '0'
            }),
            'numero_documento': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número da NF, pedido, etc. (opcional)'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Observações (opcional)'
            })
        }

    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        
        if empresa:
            # Filtrar matérias-primas por empresa
            self.fields['materia_prima'].queryset = MateriaPrima.objects.filter(
                empresa=empresa, ativo=True
            ).order_by('descricao')

    def clean_quantidade(self):
        """Validar quantidade"""
        quantidade = self.cleaned_data.get('quantidade')
        if quantidade and quantidade <= 0:
            raise ValidationError("Quantidade deve ser maior que zero.")
        return quantidade

    def clean(self):
        """Validações gerais"""
        cleaned_data = super().clean()
        tipo_movimento = cleaned_data.get('tipo_movimento')
        custo_unitario = cleaned_data.get('custo_unitario')
        
        # Validar custo unitário para entradas
        if tipo_movimento in TipoMovimentacao.get_entradas():
            if not custo_unitario or custo_unitario <= 0:
                raise ValidationError({
                    'custo_unitario': 'Custo unitário é obrigatório para entradas.'
                })
        
        return cleaned_data


class EntradaEstoqueForm(MovimentacaoEstoqueForm):
    """Form específico para entradas de estoque"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar apenas tipos de entrada
        self.fields['tipo_movimento'].choices = [
            (choice[0], choice[1]) for choice in TipoMovimentacao.choices
            if choice[0] in TipoMovimentacao.get_entradas()
        ]
        
        # Tornar custo unitário obrigatório
        self.fields['custo_unitario'].required = True


class SaidaEstoqueForm(MovimentacaoEstoqueForm):
    """Form específico para saídas de estoque"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar apenas tipos de saída
        self.fields['tipo_movimento'].choices = [
            (choice[0], choice[1]) for choice in TipoMovimentacao.choices
            if choice[0] in TipoMovimentacao.get_saidas()
        ]
        
        # Custo unitário opcional para saídas
        self.fields['custo_unitario'].required = False

    def clean(self):
        """Validações específicas para saídas"""
        cleaned_data = super().clean()
        materia_prima = cleaned_data.get('materia_prima')
        quantidade = cleaned_data.get('quantidade')
        
        # Validar estoque suficiente
        if materia_prima and quantidade:
            estoque_atual = materia_prima.quantidade_em_estoque
            if quantidade > estoque_atual:
                raise ValidationError({
                    'quantidade': f'Estoque insuficiente. Disponível: {estoque_atual} {materia_prima.unidade}'
                })
        
        return cleaned_data


class FiltroEstoqueForm(forms.Form):
    """Form para filtros na listagem de estoque"""
    
    STATUS_CHOICES = [
        ('', 'Todos'),
        ('zerado', 'Zerado'),
        ('baixo', 'Baixo'),
        ('normal', 'Normal'),
        ('alto', 'Alto'),
    ]
    
    busca = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por código ou descrição...'
        })
    )
    
    categoria = forms.ModelChoiceField(
        queryset=CategoriaMateriaPrima.objects.none(),
        required=False,
        empty_label='Todas as categorias',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    status_estoque = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    apenas_ativos = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )

    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        
        if empresa:
            self.fields['categoria'].queryset = CategoriaMateriaPrima.objects.filter(
                empresa=empresa, ativo=True
            ) 