from django import forms
from .models import MateriaPrima, MovimentacaoEstoque
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit

class MateriaPrimaForm(forms.ModelForm):
    class Meta:
        model = MateriaPrima
        fields = [
            'codigo', 'codigo_barras', 'descricao', 'unidade', 
            'fornecedor_preferencial', 'estoque_minimo', 'observacoes', 'ativo'
        ]
        widgets = {
            'observacoes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('codigo', css_class='form-group col-md-6 mb-0'),
                Column('codigo_barras', css_class='form-group col-md-6 mb-0'),
            ),
            'descricao',
            Row(
                Column('unidade', css_class='form-group col-md-4 mb-0'),
                Column('fornecedor_preferencial', css_class='form-group col-md-8 mb-0'),
            ),
            Row(
                Column('estoque_minimo', css_class='form-group col-md-6 mb-0'),
            ),
            'observacoes',
            'ativo',
            Submit('submit', 'Salvar', css_class='btn-success mt-3')
        )

class EntradaEstoqueForm(forms.Form):
    materia_prima = forms.ModelChoiceField(
        queryset=MateriaPrima.objects.none(), # Será preenchido na view
        label="Matéria-Prima"
    )
    quantidade = forms.DecimalField(
        label="Quantidade a Adicionar",
        min_value=0.001,
        decimal_places=3
    )
    custo_unitario = forms.DecimalField(
        label="Custo Unitário (R$)",
        min_value=0.0001,
        decimal_places=4
    )
    observacoes = forms.CharField(
        label="Observações (Ex: Nota Fiscal, Lote)",
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False
    )

    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)

        if empresa:
            self.fields['materia_prima'].queryset = MateriaPrima.objects.filter(empresa=empresa, ativo=True)

        self.helper = FormHelper()
        self.helper.layout = Layout(
            'materia_prima',
            Row(
                Column('quantidade', css_class='form-group col-md-6 mb-0'),
                Column('custo_unitario', css_class='form-group col-md-6 mb-0'),
            ),
            'observacoes',
            Submit('submit', 'Registrar Entrada', css_class='btn-primary mt-3')
        )
