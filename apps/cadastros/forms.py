from django import forms
from django.forms import inlineformset_factory
from .models import Cliente, Produto, Fornecedor, ProdutoMateriaPrima


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            'nome', 'nome_fantasia', 'cnpj', 'inscricao_estadual',
            'endereco', 'bairro', 'cidade', 'estado', 'cep',
            'contato_principal', 'telefone_comercial', 'telefone_celular', 'email',
            'observacoes', 'ativo'
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome ou Razão Social'}),
            'nome_fantasia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome Fantasia'}),
            'cnpj': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00.000.000/0000-00'}),
            'inscricao_estadual': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Inscrição Estadual'}),
            'endereco': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Endereço completo'}),
            'bairro': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bairro'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cidade'}),
            'estado': forms.Select(attrs={'class': 'form-control'}),
            'cep': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00000-000'}),
            'contato_principal': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do contato'}),
            'telefone_comercial': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(00) 0000-0000'}),
            'telefone_celular': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(00) 00000-0000'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@exemplo.com'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observações'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = [
            'codigo', 'tipo_produto', 'categoria', 'descricao',
            'ncm', 'tipo_grade',
            'preco_custo', 'preco_venda',
            'imagem', 'observacoes', 'ativo'
        ]
        widgets = {
            'codigo': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Código do produto (ex: PR001)',
                'readonly': True  # Será preenchido automaticamente
            }),
            'tipo_produto': forms.Select(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Descrição detalhada do produto'
            }),
            'ncm': forms.Select(attrs={'class': 'form-control'}),
            'tipo_grade': forms.Select(attrs={'class': 'form-control'}),
            'preco_custo': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'placeholder': '0,00'
            }),
            'preco_venda': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'placeholder': '0,00'
            }),
            'imagem': forms.FileInput(attrs={
                'class': 'form-control', 
                'accept': 'image/*'
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Observações'
            }),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        
        if empresa:
            # Filtrar opções por empresa
            self.fields['tipo_produto'].queryset = self.fields['tipo_produto'].queryset.filter(empresa=empresa, ativo=True)
            self.fields['categoria'].queryset = self.fields['categoria'].queryset.filter(empresa=empresa, ativo=True)
            self.fields['ncm'].queryset = self.fields['ncm'].queryset.filter(empresa=empresa, ativo=True)
            self.fields['tipo_grade'].queryset = self.fields['tipo_grade'].queryset.filter(empresa=empresa, ativo=True)


class FornecedorForm(forms.ModelForm):
    class Meta:
        model = Fornecedor
        fields = [
            'razao_social', 'nome_fantasia', 'tipo_fornecedor', 'cnpj_cpf', 'inscricao_estadual',
            'endereco', 'bairro', 'cidade', 'uf', 'cep',
            'contato_principal', 'telefone', 'email',
            'banco', 'agencia', 'conta',
            'observacoes', 'ativo'
        ]
        widgets = {
            'razao_social': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Razão Social'}),
            'nome_fantasia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome Fantasia'}),
            'tipo_fornecedor': forms.Select(attrs={'class': 'form-control'}),
            'cnpj_cpf': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00.000.000/0000-00 ou 000.000.000-00'}),
            'inscricao_estadual': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Inscrição Estadual'}),
            'endereco': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Endereço completo'}),
            'bairro': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bairro'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Cidade'}),
            'uf': forms.Select(attrs={'class': 'form-control'}),
            'cep': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00000-000'}),
            'contato_principal': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do contato'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(00) 00000-0000'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@exemplo.com'}),
            'banco': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do banco'}),
            'agencia': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0000'}),
            'conta': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00000-0'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observações'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProdutoMateriaPrimaForm(forms.ModelForm):
    class Meta:
        model = ProdutoMateriaPrima
        fields = ['materia_prima', 'quantidade']
        # Podemos adicionar widgets aqui para customizar a aparência se necessário
        widgets = {
            'materia_prima': forms.Select(attrs={'class': 'form-control materia-select'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control materia-quantidade'}),
        }

# Criamos um FormSet que trabalha com o relacionamento entre Produto e ProdutoMateriaPrima.
# 'extra=1' significa que ele vai renderizar um formulário extra em branco por padrão.
# 'can_delete=True' permite que o usuário marque itens para serem excluídos.
ProdutoMateriaPrimaFormSet = inlineformset_factory(
    Produto,
    ProdutoMateriaPrima,
    form=ProdutoMateriaPrimaForm,
    extra=1,
    can_delete=True,
    fk_name='produto'
) 