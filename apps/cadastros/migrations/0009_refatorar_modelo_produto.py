# Generated by Django 5.0.1 on 2025-07-09 19:41

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cadastros", "0008_produto_custo_total_materias_primas"),
        ("core", "0004_configuracaobilling_alter_planoassinatura_options_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="produto",
            options={
                "ordering": ["codigo"],
                "verbose_name": "Produto",
                "verbose_name_plural": "Produtos",
            },
        ),
        migrations.RemoveField(
            model_name="produto",
            name="codigo_cor",
        ),
        migrations.RemoveField(
            model_name="produto",
            name="consumo_fio",
        ),
        migrations.RemoveField(
            model_name="produto",
            name="consumo_linha_externa",
        ),
        migrations.RemoveField(
            model_name="produto",
            name="consumo_linha_interna",
        ),
        migrations.RemoveField(
            model_name="produto",
            name="cor",
        ),
        migrations.RemoveField(
            model_name="produto",
            name="custo_unitario",
        ),
        migrations.RemoveField(
            model_name="produto",
            name="preco_unitario",
        ),
        migrations.RemoveField(
            model_name="produto",
            name="produto",
        ),
        migrations.RemoveField(
            model_name="produto",
            name="referencia",
        ),
        migrations.RemoveField(
            model_name="produto",
            name="unidade",
        ),
        migrations.AddField(
            model_name="produto",
            name="categoria",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="cadastros.categoriaproduto",
                verbose_name="Categoria",
            ),
        ),
        migrations.AlterField(
            model_name="produto",
            name="codigo",
            field=models.CharField(
                help_text="Código automático do produto (ex: PR001, PR002, etc.)",
                max_length=20,
                verbose_name="Código",
            ),
        ),
        migrations.AlterField(
            model_name="produto",
            name="descricao",
            field=models.TextField(verbose_name="Descrição do Produto"),
        ),
        migrations.CreateModel(
            name="NCM",
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
                ("codigo", models.CharField(max_length=10, verbose_name="Código NCM")),
                (
                    "descricao",
                    models.CharField(max_length=200, verbose_name="Descrição"),
                ),
                (
                    "aliquota_ipi",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        max_digits=5,
                        verbose_name="Alíquota IPI (%)",
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
            ],
            options={
                "verbose_name": "NCM",
                "verbose_name_plural": "NCMs",
                "ordering": ["codigo"],
                "unique_together": {("empresa", "codigo")},
            },
        ),
        migrations.AddField(
            model_name="produto",
            name="ncm",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="cadastros.ncm",
                verbose_name="NCM",
            ),
        ),
        migrations.CreateModel(
            name="TipoGrade",
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
                        max_length=50, verbose_name="Nome do Tipo de Grade"
                    ),
                ),
                ("descricao", models.TextField(blank=True, verbose_name="Descrição")),
                (
                    "tipo",
                    models.CharField(
                        choices=[
                            ("NUMEROS", "Números (36, 38, 40, 42, etc.)"),
                            ("LETRAS", "Letras (PP, P, M, G, GG, etc.)"),
                            ("IDADE", "Idade (2, 4, 6, 8, 10, etc.)"),
                            ("PERSONALIZADO", "Personalizado"),
                        ],
                        default="LETRAS",
                        max_length=15,
                        verbose_name="Tipo",
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
            ],
            options={
                "verbose_name": "Tipo de Grade",
                "verbose_name_plural": "Tipos de Grades",
                "ordering": ["nome"],
                "unique_together": {("empresa", "nome")},
            },
        ),
        migrations.AddField(
            model_name="produto",
            name="tipo_grade",
            field=models.ForeignKey(
                blank=True,
                help_text="Define o tipo de grade de tamanhos para este produto",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="cadastros.tipograde",
                verbose_name="Tipo de Grade",
            ),
        ),
        migrations.CreateModel(
            name="TipoProduto",
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
                ("nome", models.CharField(max_length=50, verbose_name="Nome do Tipo")),
                ("descricao", models.TextField(blank=True, verbose_name="Descrição")),
                (
                    "cor_hex",
                    models.CharField(
                        default="#3b82f6",
                        help_text="Cor hexadecimal para identificação visual",
                        max_length=7,
                        verbose_name="Cor",
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
            ],
            options={
                "verbose_name": "Tipo de Produto",
                "verbose_name_plural": "Tipos de Produtos",
                "ordering": ["nome"],
                "unique_together": {("empresa", "nome")},
            },
        ),
        migrations.AddField(
            model_name="produto",
            name="tipo_produto",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="cadastros.tipoproduto",
                verbose_name="Tipo de Produto",
            ),
        ),
        migrations.CreateModel(
            name="ValorGrade",
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
                ("valor", models.CharField(max_length=10, verbose_name="Valor")),
                (
                    "descricao",
                    models.CharField(
                        blank=True, max_length=50, verbose_name="Descrição"
                    ),
                ),
                (
                    "ordem",
                    models.IntegerField(default=1, verbose_name="Ordem de Exibição"),
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
                    "tipo_grade",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="valores",
                        to="cadastros.tipograde",
                        verbose_name="Tipo de Grade",
                    ),
                ),
            ],
            options={
                "verbose_name": "Valor de Grade",
                "verbose_name_plural": "Valores de Grades",
                "ordering": ["tipo_grade", "ordem", "valor"],
                "unique_together": {("tipo_grade", "valor")},
            },
        ),
    ]
