from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.producao.models import OrdemProducao, StatusOP
from apps.financeiro.models import ContaReceber
from apps.cadastros.models import Cliente, Produto
from apps.core.models import Empresa


class Command(BaseCommand):
    help = 'Testa a automação de criação de contas a receber ao finalizar OPs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--empresa-id',
            type=int,
            help='ID da empresa para teste',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Iniciando teste de automação de faturamento...')
        )

        # Buscar empresa
        if options['empresa_id']:
            try:
                empresa = Empresa.objects.get(id=options['empresa_id'])
            except Empresa.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'❌ Empresa com ID {options["empresa_id"]} não encontrada')
                )
                return
        else:
            empresa = Empresa.objects.first()
            if not empresa:
                self.stdout.write(
                    self.style.ERROR('❌ Nenhuma empresa encontrada no sistema')
                )
                return

        self.stdout.write(f'🏢 Usando empresa: {empresa.nome}')

        # Buscar OP em produção para testar
        op_teste = OrdemProducao.objects.filter(
            empresa=empresa,
            status=StatusOP.EM_PRODUCAO
        ).first()

        if not op_teste:
            # Criar OP de teste se não existir
            cliente = Cliente.objects.filter(empresa=empresa).first()
            if not cliente:
                self.stdout.write(
                    self.style.WARNING('⚠️ Criando cliente de teste...')
                )
                # Não especificar created_at - deixar o auto_now_add funcionar
                cliente = Cliente.objects.create(
                    empresa=empresa,
                    nome='Cliente Teste Automação',
                    cnpj='12.345.678/0001-90',
                    contato_principal='Responsável Teste',
                    telefone_comercial='(11) 99999-9999',
                    telefone_celular='(11) 88888-8888',
                    email='teste@automacao.com',
                    endereco='Rua Teste, 123',
                    bairro='Centro',
                    cidade='São Paulo',
                    estado='SP',
                    cep='01000-000'
                )

            produto = Produto.objects.filter(empresa=empresa).first()
            if not produto:
                self.stdout.write(
                    self.style.WARNING('⚠️ Criando produto de teste...')
                )
                produto = Produto.objects.create(
                    empresa=empresa,
                    codigo='TESTE-001',
                    descricao='Produto criado para teste de automação',
                    preco_custo=100.00,
                    preco_venda=150.00
                )

            # Criar OP de teste
            self.stdout.write(
                self.style.WARNING('⚠️ Criando OP de teste...')
            )
            op_teste = OrdemProducao.objects.create(
                empresa=empresa,
                cliente=cliente,
                produto=produto,
                data_previsao=timezone.now().date(),
                preco_unitario=produto.preco_venda or 100.00,
                status=StatusOP.EM_PRODUCAO,
                observacoes='OP criada para teste de automação'
            )

        self.stdout.write(f'📋 OP de teste: {op_teste.numero_op}')

        # Verificar se já existe conta para esta OP
        conta_existente = ContaReceber.objects.filter(ordem_producao=op_teste).first()
        if conta_existente:
            self.stdout.write(
                self.style.WARNING(f'⚠️ Já existe conta para esta OP: {conta_existente.numero_conta}')
            )

        # Contar contas antes da finalização
        contas_antes = ContaReceber.objects.filter(empresa=empresa).count()
        self.stdout.write(f'📊 Contas a receber antes: {contas_antes}')

        # FINALIZAR A OP (isso deve triggerar a automação)
        self.stdout.write(
            self.style.WARNING('🔄 Finalizando OP para testar automação...')
        )
        
        op_teste.status = StatusOP.CONCLUIDA
        op_teste.porcentagem_concluida = 100
        op_teste.save()

        # Verificar se conta foi criada automaticamente
        contas_depois = ContaReceber.objects.filter(empresa=empresa).count()
        self.stdout.write(f'📊 Contas a receber depois: {contas_depois}')

        if contas_depois > contas_antes:
            nova_conta = ContaReceber.objects.filter(ordem_producao=op_teste).first()
            if nova_conta:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ SUCESSO! Conta {nova_conta.numero_conta} criada automaticamente!')
                )
                self.stdout.write(f'   📋 Cliente: {nova_conta.cliente.nome}')
                self.stdout.write(f'   💰 Valor: R$ {nova_conta.valor_total}')
                self.stdout.write(f'   📅 Vencimento: {nova_conta.data_vencimento}')
                self.stdout.write(f'   🏷️ Status: {nova_conta.get_status_display()}')
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Conta criada mas não vinculada à OP')
                )
        else:
            self.stdout.write(
                self.style.ERROR('❌ FALHA! Conta não foi criada automaticamente')
            )

        self.stdout.write(
            self.style.SUCCESS('🏁 Teste de automação concluído!')
        ) 