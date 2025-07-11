# Generated by Django 5.0.1 on 2025-07-04 02:54

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_configuracaobilling_alter_planoassinatura_options_and_more"),
        ("financeiro", "0002_alter_contareceber_ordem_producao"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CategoriaContaPagar",
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
                    models.CharField(max_length=100, verbose_name="Nome da Categoria"),
                ),
                ("descricao", models.TextField(blank=True, verbose_name="Descrição")),
                (
                    "codigo",
                    models.CharField(
                        blank=True,
                        help_text="Código contábil da categoria",
                        max_length=20,
                        verbose_name="Código",
                    ),
                ),
                ("ativo", models.BooleanField(default=True, verbose_name="Ativo")),
                (
                    "dedutivel",
                    models.BooleanField(
                        default=True,
                        help_text="Se a despesa é dedutível para fins fiscais",
                        verbose_name="Dedutível",
                    ),
                ),
                (
                    "centro_custo",
                    models.CharField(
                        blank=True, max_length=50, verbose_name="Centro de Custo Padrão"
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
                "verbose_name": "Categoria de Conta a Pagar",
                "verbose_name_plural": "Categorias de Contas a Pagar",
                "ordering": ["nome"],
                "unique_together": {("empresa", "nome")},
            },
        ),
        migrations.CreateModel(
            name="ContaPagar",
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
                    "fornecedor_nome",
                    models.CharField(max_length=200, verbose_name="Fornecedor"),
                ),
                (
                    "fornecedor_documento",
                    models.CharField(
                        blank=True, max_length=20, verbose_name="CNPJ/CPF do Fornecedor"
                    ),
                ),
                (
                    "numero_documento",
                    models.CharField(max_length=50, verbose_name="Número do Documento"),
                ),
                (
                    "tipo_documento",
                    models.CharField(
                        choices=[
                            ("NF", "Nota Fiscal"),
                            ("BOL", "Boleto"),
                            ("FAT", "Fatura"),
                            ("REC", "Recibo"),
                            ("CTR", "Contrato"),
                            ("OUT", "Outros"),
                        ],
                        default="NF",
                        max_length=3,
                        verbose_name="Tipo de Documento",
                    ),
                ),
                (
                    "descricao",
                    models.CharField(max_length=300, verbose_name="Descrição"),
                ),
                (
                    "valor_original",
                    models.DecimalField(
                        decimal_places=2, max_digits=12, verbose_name="Valor Original"
                    ),
                ),
                (
                    "valor_juros",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=12,
                        verbose_name="Juros/Multa",
                    ),
                ),
                (
                    "valor_desconto",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=12,
                        verbose_name="Desconto",
                    ),
                ),
                (
                    "valor_pago",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=12,
                        verbose_name="Valor Pago",
                    ),
                ),
                ("data_emissao", models.DateField(verbose_name="Data de Emissão")),
                (
                    "data_vencimento",
                    models.DateField(verbose_name="Data de Vencimento"),
                ),
                (
                    "data_pagamento",
                    models.DateField(
                        blank=True, null=True, verbose_name="Data de Pagamento"
                    ),
                ),
                (
                    "parcelado",
                    models.BooleanField(default=False, verbose_name="Parcelado"),
                ),
                (
                    "numero_parcelas",
                    models.IntegerField(default=1, verbose_name="Número de Parcelas"),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDENTE", "Pendente"),
                            ("PARCIAL", "Parcialmente Pago"),
                            ("PAGO", "Pago"),
                            ("VENCIDO", "Vencido"),
                            ("CANCELADO", "Cancelado"),
                            ("AGENDADO", "Agendado"),
                        ],
                        default="PENDENTE",
                        max_length=20,
                        verbose_name="Status",
                    ),
                ),
                (
                    "recorrente",
                    models.BooleanField(default=False, verbose_name="Conta Recorrente"),
                ),
                (
                    "banco_pagamento",
                    models.CharField(blank=True, max_length=100, verbose_name="Banco"),
                ),
                (
                    "agencia_pagamento",
                    models.CharField(blank=True, max_length=10, verbose_name="Agência"),
                ),
                (
                    "conta_pagamento",
                    models.CharField(blank=True, max_length=20, verbose_name="Conta"),
                ),
                (
                    "centro_custo",
                    models.CharField(
                        blank=True, max_length=50, verbose_name="Centro de Custo"
                    ),
                ),
                (
                    "arquivo_documento",
                    models.FileField(
                        blank=True,
                        null=True,
                        upload_to="contas_pagar/documentos/%Y/%m/",
                        verbose_name="Arquivo do Documento",
                    ),
                ),
                (
                    "observacoes",
                    models.TextField(blank=True, verbose_name="Observações"),
                ),
                (
                    "data_aprovacao",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Data de Aprovação"
                    ),
                ),
                (
                    "aprovado_por",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="contas_pagar_aprovadas",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Aprovado por",
                    ),
                ),
                (
                    "categoria",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="financeiro.categoriacontapagar",
                        verbose_name="Categoria",
                    ),
                ),
                (
                    "conta_origem",
                    models.ForeignKey(
                        blank=True,
                        help_text="Conta que originou esta conta recorrente",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="contas_recorrentes",
                        to="financeiro.contapagar",
                        verbose_name="Conta Origem",
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
                (
                    "usuario_criacao",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="contas_pagar_criadas",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Criado por",
                    ),
                ),
            ],
            options={
                "verbose_name": "Conta a Pagar",
                "verbose_name_plural": "Contas a Pagar",
                "ordering": ["data_vencimento", "-data_emissao"],
            },
        ),
        migrations.CreateModel(
            name="ParcelaContaPagar",
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
                    "numero_parcela",
                    models.IntegerField(verbose_name="Número da Parcela"),
                ),
                (
                    "valor",
                    models.DecimalField(
                        decimal_places=2, max_digits=12, verbose_name="Valor da Parcela"
                    ),
                ),
                (
                    "valor_pago",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=12,
                        verbose_name="Valor Pago",
                    ),
                ),
                (
                    "data_vencimento",
                    models.DateField(verbose_name="Data de Vencimento"),
                ),
                (
                    "data_pagamento",
                    models.DateField(
                        blank=True, null=True, verbose_name="Data de Pagamento"
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDENTE", "Pendente"),
                            ("PARCIAL", "Parcialmente Pago"),
                            ("PAGO", "Pago"),
                            ("VENCIDO", "Vencido"),
                            ("CANCELADO", "Cancelado"),
                            ("AGENDADO", "Agendado"),
                        ],
                        default="PENDENTE",
                        max_length=20,
                        verbose_name="Status",
                    ),
                ),
                (
                    "observacoes",
                    models.TextField(blank=True, verbose_name="Observações"),
                ),
                (
                    "conta_pagar",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="parcelas",
                        to="financeiro.contapagar",
                        verbose_name="Conta a Pagar",
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
                "verbose_name": "Parcela de Conta a Pagar",
                "verbose_name_plural": "Parcelas de Contas a Pagar",
                "ordering": ["conta_pagar", "numero_parcela"],
                "unique_together": {("conta_pagar", "numero_parcela")},
            },
        ),
        migrations.CreateModel(
            name="PagamentoEfetuado",
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
                    "valor",
                    models.DecimalField(
                        decimal_places=2, max_digits=12, verbose_name="Valor Pago"
                    ),
                ),
                ("data_pagamento", models.DateField(verbose_name="Data do Pagamento")),
                (
                    "forma_pagamento",
                    models.CharField(
                        choices=[
                            ("DINHEIRO", "Dinheiro"),
                            ("PIX", "PIX"),
                            ("TRANSFERENCIA", "Transferência"),
                            ("CARTAO_CREDITO", "Cartão de Crédito"),
                            ("CARTAO_DEBITO", "Cartão de Débito"),
                            ("BOLETO", "Boleto"),
                            ("CHEQUE", "Cheque"),
                        ],
                        max_length=20,
                        verbose_name="Forma de Pagamento",
                    ),
                ),
                (
                    "banco",
                    models.CharField(blank=True, max_length=100, verbose_name="Banco"),
                ),
                (
                    "agencia",
                    models.CharField(blank=True, max_length=10, verbose_name="Agência"),
                ),
                (
                    "conta",
                    models.CharField(blank=True, max_length=20, verbose_name="Conta"),
                ),
                (
                    "numero_transacao",
                    models.CharField(
                        blank=True, max_length=100, verbose_name="Número da Transação"
                    ),
                ),
                (
                    "comprovante",
                    models.FileField(
                        blank=True,
                        null=True,
                        upload_to="contas_pagar/comprovantes/%Y/%m/",
                        verbose_name="Comprovante de Pagamento",
                    ),
                ),
                (
                    "observacoes",
                    models.TextField(blank=True, verbose_name="Observações"),
                ),
                (
                    "conta_pagar",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="pagamentos_efetuados",
                        to="financeiro.contapagar",
                        verbose_name="Conta a Pagar",
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
                (
                    "usuario_pagamento",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Pago por",
                    ),
                ),
                (
                    "parcela",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="pagamentos",
                        to="financeiro.parcelacontapagar",
                        verbose_name="Parcela",
                    ),
                ),
            ],
            options={
                "verbose_name": "Pagamento Efetuado",
                "verbose_name_plural": "Pagamentos Efetuados",
                "ordering": ["-data_pagamento"],
            },
        ),
        migrations.CreateModel(
            name="SubcategoriaContaPagar",
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
                    models.CharField(
                        max_length=100, verbose_name="Nome da Subcategoria"
                    ),
                ),
                ("descricao", models.TextField(blank=True, verbose_name="Descrição")),
                (
                    "codigo",
                    models.CharField(
                        blank=True,
                        help_text="Código contábil da subcategoria",
                        max_length=20,
                        verbose_name="Código",
                    ),
                ),
                ("ativo", models.BooleanField(default=True, verbose_name="Ativo")),
                (
                    "recorrente",
                    models.BooleanField(
                        default=False,
                        help_text="Se esta despesa se repete mensalmente",
                        verbose_name="Despesa Recorrente",
                    ),
                ),
                (
                    "dia_vencimento_padrao",
                    models.IntegerField(
                        blank=True,
                        help_text="Dia do mês para vencimento (1-31)",
                        null=True,
                        verbose_name="Dia de Vencimento Padrão",
                    ),
                ),
                (
                    "categoria",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="subcategorias",
                        to="financeiro.categoriacontapagar",
                        verbose_name="Categoria",
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
                "verbose_name": "Subcategoria de Conta a Pagar",
                "verbose_name_plural": "Subcategorias de Contas a Pagar",
                "ordering": ["categoria", "nome"],
                "unique_together": {("empresa", "categoria", "nome")},
            },
        ),
        migrations.AddField(
            model_name="contapagar",
            name="subcategoria",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="financeiro.subcategoriacontapagar",
                verbose_name="Subcategoria",
            ),
        ),
        migrations.AddIndex(
            model_name="contapagar",
            index=models.Index(
                fields=["empresa", "status", "data_vencimento"],
                name="financeiro__empresa_c2d216_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="contapagar",
            index=models.Index(
                fields=["empresa", "categoria", "subcategoria"],
                name="financeiro__empresa_fc07cc_idx",
            ),
        ),
    ]
