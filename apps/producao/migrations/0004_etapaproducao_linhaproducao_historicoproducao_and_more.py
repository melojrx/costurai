# Generated by Django 5.0.1 on 2025-07-04 02:13

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_configuracaobilling_alter_planoassinatura_options_and_more"),
        ("producao", "0003_alter_gradeproducao_options_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="EtapaProducao",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Criado em"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Atualizado em"),
                ),
                (
                    "nome",
                    models.CharField(max_length=100, verbose_name="Nome da Etapa"),
                ),
                ("descricao", models.TextField(blank=True, verbose_name="Descrição")),
                (
                    "ordem",
                    models.IntegerField(
                        help_text="Ordem de execução da etapa", verbose_name="Ordem"
                    ),
                ),
                (
                    "tempo_medio_minutos",
                    models.IntegerField(
                        default=60,
                        help_text="Tempo médio para completar a etapa",
                        verbose_name="Tempo Médio (min)",
                    ),
                ),
                (
                    "requer_aprovacao",
                    models.BooleanField(
                        default=False,
                        help_text="Se marcado, a etapa precisa ser aprovada para avançar",
                        verbose_name="Requer Aprovação",
                    ),
                ),
                (
                    "cor_hex",
                    models.CharField(
                        default="#3b82f6",
                        help_text="Cor hexadecimal para representar a etapa",
                        max_length=7,
                        verbose_name="Cor",
                    ),
                ),
                (
                    "icone",
                    models.CharField(
                        default="fas fa-cog",
                        help_text="Classe do ícone FontAwesome",
                        max_length=50,
                        verbose_name="Ícone",
                    ),
                ),
                ("ativo", models.BooleanField(default=True, verbose_name="Ativo")),
                (
                    "departamento",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="producao.departamento",
                        verbose_name="Departamento Responsável",
                    ),
                ),
                (
                    "empresa",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="core.empresa",
                        verbose_name="Empresa",
                    ),
                ),
            ],
            options={
                "verbose_name": "Etapa de Produção",
                "verbose_name_plural": "Etapas de Produção",
                "ordering": ["ordem"],
                "unique_together": {("empresa", "nome")},
            },
        ),
        migrations.CreateModel(
            name="LinhaProducao",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Criado em"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Atualizado em"),
                ),
                (
                    "nome",
                    models.CharField(max_length=100, verbose_name="Nome da Linha"),
                ),
                ("descricao", models.TextField(blank=True, verbose_name="Descrição")),
                (
                    "capacidade_diaria",
                    models.IntegerField(
                        default=100,
                        help_text="Número de peças por dia",
                        verbose_name="Capacidade Diária",
                    ),
                ),
                (
                    "capacidade_horaria",
                    models.IntegerField(
                        default=12,
                        help_text="Número de peças por hora",
                        verbose_name="Capacidade Horária",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("ATIVA", "Ativa"),
                            ("PARADA", "Parada"),
                            ("MANUTENCAO", "Manutenção"),
                            ("INATIVA", "Inativa"),
                        ],
                        default="ATIVA",
                        max_length=20,
                        verbose_name="Status",
                    ),
                ),
                (
                    "horas_trabalho_dia",
                    models.DecimalField(
                        decimal_places=2,
                        default=8.0,
                        max_digits=4,
                        verbose_name="Horas de Trabalho/Dia",
                    ),
                ),
                (
                    "dias_trabalho_semana",
                    models.IntegerField(
                        default=5, verbose_name="Dias de Trabalho/Semana"
                    ),
                ),
                (
                    "data_ultima_producao",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Última Produção"
                    ),
                ),
                (
                    "data_proxima_manutencao",
                    models.DateField(
                        blank=True, null=True, verbose_name="Próxima Manutenção"
                    ),
                ),
                (
                    "total_pecas_produzidas",
                    models.IntegerField(
                        default=0, verbose_name="Total de Peças Produzidas"
                    ),
                ),
                (
                    "eficiencia_media",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=5,
                        verbose_name="Eficiência Média (%)",
                    ),
                ),
                ("ativo", models.BooleanField(default=True, verbose_name="Ativo")),
                (
                    "empresa",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="core.empresa",
                        verbose_name="Empresa",
                    ),
                ),
                (
                    "operadores",
                    models.ManyToManyField(
                        blank=True,
                        related_name="linhas_operador",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Operadores",
                    ),
                ),
                (
                    "responsavel",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="linhas_responsavel",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Responsável",
                    ),
                ),
            ],
            options={
                "verbose_name": "Linha de Produção",
                "verbose_name_plural": "Linhas de Produção",
                "ordering": ["nome"],
                "unique_together": {("empresa", "nome")},
            },
        ),
        migrations.CreateModel(
            name="HistoricoProducao",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Criado em"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Atualizado em"),
                ),
                (
                    "status_anterior",
                    models.CharField(
                        choices=[
                            ("NAO_INICIADA", "Não Iniciada"),
                            ("EM_ANDAMENTO", "Em Andamento"),
                            ("CONCLUIDA", "Concluída"),
                            ("PAUSADA", "Pausada"),
                            ("CANCELADA", "Cancelada"),
                        ],
                        max_length=20,
                        verbose_name="Status Anterior",
                    ),
                ),
                (
                    "status_atual",
                    models.CharField(
                        choices=[
                            ("NAO_INICIADA", "Não Iniciada"),
                            ("EM_ANDAMENTO", "Em Andamento"),
                            ("CONCLUIDA", "Concluída"),
                            ("PAUSADA", "Pausada"),
                            ("CANCELADA", "Cancelada"),
                        ],
                        max_length=20,
                        verbose_name="Status Atual",
                    ),
                ),
                (
                    "quantidade_produzida",
                    models.IntegerField(default=0, verbose_name="Quantidade Produzida"),
                ),
                (
                    "quantidade_defeituosa",
                    models.IntegerField(
                        default=0, verbose_name="Quantidade Defeituosa"
                    ),
                ),
                (
                    "quantidade_retrabalho",
                    models.IntegerField(
                        default=0, verbose_name="Quantidade Retrabalho"
                    ),
                ),
                ("data_inicio", models.DateTimeField(verbose_name="Data/Hora Início")),
                (
                    "data_fim",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Data/Hora Fim"
                    ),
                ),
                (
                    "tempo_producao_minutos",
                    models.IntegerField(default=0, verbose_name="Tempo Produção (min)"),
                ),
                (
                    "observacoes",
                    models.TextField(blank=True, verbose_name="Observações"),
                ),
                (
                    "problemas_encontrados",
                    models.TextField(blank=True, verbose_name="Problemas Encontrados"),
                ),
                (
                    "aprovado",
                    models.BooleanField(default=True, verbose_name="Aprovado"),
                ),
                (
                    "data_aprovacao",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Data Aprovação"
                    ),
                ),
                (
                    "data_registro",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Data de Registro"
                    ),
                ),
                (
                    "aprovado_por",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="aprovacoes_producao",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Aprovado Por",
                    ),
                ),
                (
                    "etapa",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="producao.etapaproducao",
                        verbose_name="Etapa",
                    ),
                ),
                (
                    "operador",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Operador",
                    ),
                ),
                (
                    "ordem_producao",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="historicos_producao",
                        to="producao.ordemproducao",
                        verbose_name="Ordem de Produção",
                    ),
                ),
                (
                    "supervisor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="supervisoes_producao",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Supervisor",
                    ),
                ),
                (
                    "linha_producao",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="historicos_producao",
                        to="producao.linhaproducao",
                        verbose_name="Linha de Produção",
                    ),
                ),
            ],
            options={
                "verbose_name": "Histórico de Produção",
                "verbose_name_plural": "Históricos de Produção",
                "ordering": ["-data_registro"],
            },
        ),
        migrations.AddField(
            model_name="ordemproducao",
            name="linha_producao",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="ops_linha",
                to="producao.linhaproducao",
                verbose_name="Linha de Produção",
            ),
        ),
        migrations.CreateModel(
            name="ControleEtapaOP",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Criado em"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Atualizado em"),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("NAO_INICIADA", "Não Iniciada"),
                            ("EM_ANDAMENTO", "Em Andamento"),
                            ("CONCLUIDA", "Concluída"),
                            ("PAUSADA", "Pausada"),
                            ("CANCELADA", "Cancelada"),
                        ],
                        default="NAO_INICIADA",
                        max_length=20,
                        verbose_name="Status",
                    ),
                ),
                (
                    "porcentagem_concluida",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=5,
                        verbose_name="% Concluída",
                    ),
                ),
                (
                    "quantidade_planejada",
                    models.IntegerField(verbose_name="Quantidade Planejada"),
                ),
                (
                    "quantidade_produzida",
                    models.IntegerField(default=0, verbose_name="Quantidade Produzida"),
                ),
                (
                    "data_inicio",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Data Início"
                    ),
                ),
                (
                    "data_fim",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Data Fim"
                    ),
                ),
                (
                    "data_prevista",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Data Prevista"
                    ),
                ),
                (
                    "observacoes",
                    models.TextField(blank=True, verbose_name="Observações"),
                ),
                (
                    "ordem_producao",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="controles_etapa",
                        to="producao.ordemproducao",
                        verbose_name="Ordem de Produção",
                    ),
                ),
                (
                    "responsavel",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Responsável",
                    ),
                ),
                (
                    "etapa",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="producao.etapaproducao",
                        verbose_name="Etapa",
                    ),
                ),
                (
                    "linha_producao",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="producao.linhaproducao",
                        verbose_name="Linha de Produção",
                    ),
                ),
            ],
            options={
                "verbose_name": "Controle de Etapa OP",
                "verbose_name_plural": "Controles de Etapa OP",
                "ordering": ["etapa__ordem"],
                "unique_together": {("ordem_producao", "etapa")},
            },
        ),
    ]
