from django.core.management.base import BaseCommand
from django.db import transaction
from django.apps import apps


class Command(BaseCommand):
    help = 'Migra dados de estoque do app producao para o app estoque'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Executa sem fazer alterações no banco',
        )
        parser.add_argument(
            '--empresa-id',
            type=int,
            help='ID da empresa específica para migrar (opcional)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        empresa_id = options.get('empresa_id')
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('MODO DRY-RUN: Nenhuma alteração será feita no banco')
            )
        
        try:
            with transaction.atomic():
                # Migrar MateriaPrima
                self.migrar_materias_primas(empresa_id, dry_run)
                
                # Migrar MovimentacaoEstoque
                self.migrar_movimentacoes_estoque(empresa_id, dry_run)
                
                if dry_run:
                    # Forçar rollback no dry-run
                    transaction.set_rollback(True)
                    self.stdout.write(
                        self.style.SUCCESS('DRY-RUN concluído com sucesso!')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS('Migração concluída com sucesso!')
                    )
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Erro durante a migração: {str(e)}')
            )
            raise

    def migrar_materias_primas(self, empresa_id, dry_run):
        """Migra MateriaPrima do app producao para estoque"""
        
        # Obter modelos
        MateriaPrimaOld = apps.get_model('producao', 'MateriaPrima')
        MateriaPrimaNew = apps.get_model('estoque', 'MateriaPrima')
        
        # Filtrar por empresa se especificado
        queryset = MateriaPrimaOld.objects.all()
        if empresa_id:
            queryset = queryset.filter(empresa_id=empresa_id)
        
        total = queryset.count()
        migradas = 0
        
        self.stdout.write(f'Migrando {total} matérias-primas...')
        
        for mp_old in queryset:
            # Verificar se já existe no novo app
            if MateriaPrimaNew.objects.filter(
                empresa=mp_old.empresa,
                codigo=mp_old.codigo
            ).exists():
                self.stdout.write(
                    self.style.WARNING(
                        f'Matéria-prima {mp_old.codigo} já existe no novo app'
                    )
                )
                continue
            
            if not dry_run:
                # Criar no novo app
                MateriaPrimaNew.objects.create(
                    empresa=mp_old.empresa,
                    codigo=mp_old.codigo,
                    codigo_barras=getattr(mp_old, 'codigo_barras', None),
                    descricao=mp_old.descricao,
                    categoria=None,  # Será mapeado depois se necessário
                    unidade=mp_old.unidade,
                    fornecedor_preferencial=getattr(mp_old, 'fornecedor_preferencial', None),
                    estoque_minimo=getattr(mp_old, 'estoque_minimo', 0),
                    estoque_maximo=getattr(mp_old, 'estoque_maximo', 0),
                    custo_medio_ponderado=getattr(mp_old, 'custo_medio_ponderado', 0),
                    custo_ultima_compra=getattr(mp_old, 'custo_ultima_compra', 0),
                    controlar_lote=getattr(mp_old, 'controlar_lote', False),
                    tem_validade=getattr(mp_old, 'tem_validade', False),
                    observacoes=getattr(mp_old, 'observacoes', ''),
                    ativo=mp_old.ativo,
                    created_at=mp_old.created_at,
                    updated_at=mp_old.updated_at,
                )
            
            migradas += 1
            
            if migradas % 100 == 0:
                self.stdout.write(f'Processadas {migradas}/{total} matérias-primas')
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ {migradas} matérias-primas migradas')
        )

    def migrar_movimentacoes_estoque(self, empresa_id, dry_run):
        """Migra MovimentacaoEstoque do app producao para estoque"""
        
        # Obter modelos
        MovimentacaoOld = apps.get_model('producao', 'MovimentacaoEstoque')
        MovimentacaoNew = apps.get_model('estoque', 'MovimentacaoEstoque')
        MateriaPrimaNew = apps.get_model('estoque', 'MateriaPrima')
        
        # Filtrar por empresa se especificado
        queryset = MovimentacaoOld.objects.all()
        if empresa_id:
            queryset = queryset.filter(empresa_id=empresa_id)
        
        total = queryset.count()
        migradas = 0
        
        self.stdout.write(f'Migrando {total} movimentações de estoque...')
        
        for mov_old in queryset:
            # Buscar matéria-prima correspondente no novo app
            try:
                materia_prima_new = MateriaPrimaNew.objects.get(
                    empresa=mov_old.empresa,
                    codigo=mov_old.materia_prima.codigo
                )
            except MateriaPrimaNew.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f'Matéria-prima {mov_old.materia_prima.codigo} não encontrada no novo app'
                    )
                )
                continue
            
            # Verificar se já existe
            if MovimentacaoNew.objects.filter(
                empresa=mov_old.empresa,
                materia_prima=materia_prima_new,
                data_movimento=mov_old.data_movimento,
                quantidade=mov_old.quantidade,
                tipo_movimento=mov_old.tipo_movimento
            ).exists():
                continue
            
            if not dry_run:
                # Criar no novo app
                MovimentacaoNew.objects.create(
                    empresa=mov_old.empresa,
                    materia_prima=materia_prima_new,
                    data_movimento=mov_old.data_movimento,
                    tipo_movimento=mov_old.tipo_movimento,
                    quantidade=mov_old.quantidade,
                    custo_unitario=getattr(mov_old, 'custo_unitario', 0),
                    numero_documento=getattr(mov_old, 'numero_documento', ''),
                    lote=None,  # Será mapeado depois se necessário
                    usuario=getattr(mov_old, 'usuario', None),
                    observacoes=getattr(mov_old, 'observacoes', ''),
                    motivo_ajuste=getattr(mov_old, 'motivo_ajuste', ''),
                    cancelada=getattr(mov_old, 'cancelada', False),
                    created_at=mov_old.created_at,
                    updated_at=mov_old.updated_at,
                )
            
            migradas += 1
            
            if migradas % 1000 == 0:
                self.stdout.write(f'Processadas {migradas}/{total} movimentações')
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ {migradas} movimentações migradas')
        ) 