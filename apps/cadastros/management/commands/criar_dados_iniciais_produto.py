from django.core.management.base import BaseCommand
from django.db import transaction
from apps.core.models import Empresa
from apps.cadastros.models import TipoProduto, NCM, TipoGrade, ValorGrade


class Command(BaseCommand):
    help = 'Cria dados iniciais para os novos modelos de produto'

    def add_arguments(self, parser):
        parser.add_argument(
            '--empresa-id',
            type=int,
            help='ID da empresa para criar os dados (se não informado, cria para todas)',
        )

    def handle(self, *args, **options):
        empresa_id = options.get('empresa_id')
        
        if empresa_id:
            empresas = Empresa.objects.filter(id=empresa_id)
            if not empresas.exists():
                self.stdout.write(
                    self.style.ERROR(f'Empresa com ID {empresa_id} não encontrada')
                )
                return
        else:
            empresas = Empresa.objects.all()
        
        for empresa in empresas:
            self.stdout.write(f'Criando dados iniciais para empresa: {empresa.nome}')
            self.criar_dados_empresa(empresa)
        
        self.stdout.write(
            self.style.SUCCESS('Dados iniciais criados com sucesso!')
        )

    def criar_dados_empresa(self, empresa):
        with transaction.atomic():
            # 1. Criar Tipos de Produto
            tipos_produto = [
                {'nome': 'Calça', 'descricao': 'Calças em geral', 'cor_hex': '#3b82f6'},
                {'nome': 'Blusa', 'descricao': 'Blusas e camisetas', 'cor_hex': '#ef4444'},
                {'nome': 'Vestido', 'descricao': 'Vestidos', 'cor_hex': '#8b5cf6'},
                {'nome': 'Shorts', 'descricao': 'Shorts e bermudas', 'cor_hex': '#10b981'},
                {'nome': 'Saia', 'descricao': 'Saias', 'cor_hex': '#f59e0b'},
                {'nome': 'Camisa', 'descricao': 'Camisas sociais', 'cor_hex': '#6b7280'},
                {'nome': 'Jaqueta', 'descricao': 'Jaquetas e casacos', 'cor_hex': '#374151'},
                {'nome': 'Outros', 'descricao': 'Outros tipos de produtos', 'cor_hex': '#9ca3af'},
            ]
            
            for tipo_data in tipos_produto:
                TipoProduto.objects.get_or_create(
                    empresa=empresa,
                    nome=tipo_data['nome'],
                    defaults={
                        'descricao': tipo_data['descricao'],
                        'cor_hex': tipo_data['cor_hex']
                    }
                )
            
            self.stdout.write(f'  ✓ Tipos de produto criados')
            
            # 2. Criar NCMs básicos para confecção
            ncms = [
                {'codigo': '6203.42.00', 'descricao': 'Calças, jardineiras, bermudas e shorts, de algodão'},
                {'codigo': '6204.62.00', 'descricao': 'Calças, jardineiras, bermudas e shorts, de algodão (feminino)'},
                {'codigo': '6205.20.00', 'descricao': 'Camisas de algodão (masculino)'},
                {'codigo': '6206.40.00', 'descricao': 'Camisas, blusas e blusões, de algodão (feminino)'},
                {'codigo': '6204.44.00', 'descricao': 'Vestidos de algodão'},
                {'codigo': '6204.52.00', 'descricao': 'Saias e saias-calças, de algodão'},
                {'codigo': '6210.10.00', 'descricao': 'Vestuário confeccionado com produtos das posições 56.02 ou 56.03'},
                {'codigo': '6211.42.00', 'descricao': 'Outros vestuários, de algodão (masculino)'},
                {'codigo': '6211.43.00', 'descricao': 'Outros vestuários, de algodão (feminino)'},
            ]
            
            for ncm_data in ncms:
                NCM.objects.get_or_create(
                    empresa=empresa,
                    codigo=ncm_data['codigo'],
                    defaults={
                        'descricao': ncm_data['descricao'],
                        'aliquota_ipi': 0
                    }
                )
            
            self.stdout.write(f'  ✓ NCMs criados')
            
            # 3. Criar Tipos de Grade
            tipos_grade = [
                {
                    'nome': 'Letras Adulto',
                    'descricao': 'Tamanhos em letras para adultos',
                    'tipo': 'LETRAS',
                    'valores': [
                        {'valor': 'PP', 'descricao': 'Extra Pequeno', 'ordem': 1},
                        {'valor': 'P', 'descricao': 'Pequeno', 'ordem': 2},
                        {'valor': 'M', 'descricao': 'Médio', 'ordem': 3},
                        {'valor': 'G', 'descricao': 'Grande', 'ordem': 4},
                        {'valor': 'GG', 'descricao': 'Extra Grande', 'ordem': 5},
                        {'valor': 'XG', 'descricao': 'Extra Extra Grande', 'ordem': 6},
                    ]
                },
                {
                    'nome': 'Números Calça',
                    'descricao': 'Numeração para calças',
                    'tipo': 'NUMEROS',
                    'valores': [
                        {'valor': '36', 'descricao': 'Tamanho 36', 'ordem': 1},
                        {'valor': '38', 'descricao': 'Tamanho 38', 'ordem': 2},
                        {'valor': '40', 'descricao': 'Tamanho 40', 'ordem': 3},
                        {'valor': '42', 'descricao': 'Tamanho 42', 'ordem': 4},
                        {'valor': '44', 'descricao': 'Tamanho 44', 'ordem': 5},
                        {'valor': '46', 'descricao': 'Tamanho 46', 'ordem': 6},
                        {'valor': '48', 'descricao': 'Tamanho 48', 'ordem': 7},
                        {'valor': '50', 'descricao': 'Tamanho 50', 'ordem': 8},
                        {'valor': '52', 'descricao': 'Tamanho 52', 'ordem': 9},
                    ]
                },
                {
                    'nome': 'Idade Infantil',
                    'descricao': 'Tamanhos por idade para crianças',
                    'tipo': 'IDADE',
                    'valores': [
                        {'valor': '2', 'descricao': '2 anos', 'ordem': 1},
                        {'valor': '4', 'descricao': '4 anos', 'ordem': 2},
                        {'valor': '6', 'descricao': '6 anos', 'ordem': 3},
                        {'valor': '8', 'descricao': '8 anos', 'ordem': 4},
                        {'valor': '10', 'descricao': '10 anos', 'ordem': 5},
                        {'valor': '12', 'descricao': '12 anos', 'ordem': 6},
                        {'valor': '14', 'descricao': '14 anos', 'ordem': 7},
                        {'valor': '16', 'descricao': '16 anos', 'ordem': 8},
                    ]
                }
            ]
            
            for grade_data in tipos_grade:
                tipo_grade, created = TipoGrade.objects.get_or_create(
                    empresa=empresa,
                    nome=grade_data['nome'],
                    defaults={
                        'descricao': grade_data['descricao'],
                        'tipo': grade_data['tipo']
                    }
                )
                
                # Criar valores da grade
                for valor_data in grade_data['valores']:
                    ValorGrade.objects.get_or_create(
                        empresa=empresa,
                        tipo_grade=tipo_grade,
                        valor=valor_data['valor'],
                        defaults={
                            'descricao': valor_data['descricao'],
                            'ordem': valor_data['ordem']
                        }
                    )
            
            self.stdout.write(f'  ✓ Tipos de grade e valores criados')
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Dados iniciais criados para {empresa.nome}')
            ) 