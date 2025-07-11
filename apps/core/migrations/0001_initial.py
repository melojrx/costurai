# Generated by Django 5.0.1 on 2025-06-24 22:35

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Empresa",
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
                    "nome",
                    models.CharField(max_length=100, verbose_name="Nome Fantasia"),
                ),
                ("razao_social", models.CharField(max_length=150)),
                ("cnpj", models.CharField(max_length=18, unique=True)),
                ("endereco", models.TextField()),
                ("cidade", models.CharField(max_length=50)),
                ("estado", models.CharField(max_length=2)),
                ("cep", models.CharField(max_length=10)),
                ("telefone", models.CharField(max_length=20)),
                ("email", models.EmailField(max_length=254)),
                (
                    "capacidade_produtiva",
                    models.IntegerField(
                        default=300, verbose_name="Capacidade Produtiva/Dia"
                    ),
                ),
                (
                    "logo",
                    models.ImageField(
                        blank=True, null=True, upload_to="empresas/logos/"
                    ),
                ),
                ("ativa", models.BooleanField(default=True)),
                ("data_cadastro", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Empresa",
                "verbose_name_plural": "Empresas",
                "ordering": ["nome"],
            },
        ),
        migrations.CreateModel(
            name="PlanoAssinatura",
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
                ("nome", models.CharField(max_length=50, unique=True)),
                (
                    "tipo",
                    models.CharField(
                        choices=[
                            ("BASICO", "Básico - R$ 49/mês"),
                            ("PROFISSIONAL", "Profissional - R$ 99/mês"),
                            ("ENTERPRISE", "Enterprise - R$ 199/mês"),
                        ],
                        max_length=15,
                    ),
                ),
                ("descricao", models.TextField()),
                ("preco_mensal", models.DecimalField(decimal_places=2, max_digits=8)),
                ("max_empresas", models.IntegerField(default=1)),
                ("max_ops_mes", models.IntegerField(default=100)),
                ("max_usuarios", models.IntegerField(default=5)),
                ("tem_api", models.BooleanField(default=False)),
                ("tem_relatorios_avancados", models.BooleanField(default=False)),
                ("tem_suporte_prioritario", models.BooleanField(default=False)),
                ("ativo", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Plano de Assinatura",
                "verbose_name_plural": "Planos de Assinatura",
                "ordering": ["preco_mensal"],
            },
        ),
        migrations.CreateModel(
            name="AuditLog",
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
                ("acao", models.CharField(max_length=50)),
                ("modelo", models.CharField(max_length=50)),
                ("registro_id", models.IntegerField()),
                ("dados_antes", models.JSONField(blank=True, null=True)),
                ("dados_depois", models.JSONField(blank=True, null=True)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.TextField(blank=True)),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                (
                    "usuario",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "empresa",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="core.empresa"
                    ),
                ),
            ],
            options={
                "verbose_name": "Log de Auditoria",
                "verbose_name_plural": "Logs de Auditoria",
                "ordering": ["-timestamp"],
            },
        ),
        migrations.CreateModel(
            name="AssinaturaEmpresa",
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
                    "status",
                    models.CharField(
                        choices=[
                            ("ATIVA", "Ativa"),
                            ("SUSPENSA", "Suspensa"),
                            ("CANCELADA", "Cancelada"),
                            ("TRIAL", "Trial"),
                        ],
                        default="TRIAL",
                        max_length=10,
                    ),
                ),
                ("data_inicio", models.DateTimeField(auto_now_add=True)),
                ("data_fim", models.DateTimeField(blank=True, null=True)),
                ("data_proximo_pagamento", models.DateField(blank=True, null=True)),
                ("trial_ativo", models.BooleanField(default=True)),
                ("trial_fim", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "empresa",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="assinatura",
                        to="core.empresa",
                    ),
                ),
                (
                    "plano",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        to="core.planoassinatura",
                    ),
                ),
            ],
            options={
                "verbose_name": "Assinatura da Empresa",
                "verbose_name_plural": "Assinaturas das Empresas",
            },
        ),
        migrations.CreateModel(
            name="UserProfile",
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
                ("telefone", models.CharField(blank=True, max_length=20)),
                ("cargo", models.CharField(blank=True, max_length=50)),
                (
                    "foto_perfil",
                    models.ImageField(
                        blank=True, null=True, upload_to="users/avatars/"
                    ),
                ),
                (
                    "timezone",
                    models.CharField(default="America/Sao_Paulo", max_length=50),
                ),
                ("idioma", models.CharField(default="pt-br", max_length=5)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="profile",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Perfil do Usuário",
                "verbose_name_plural": "Perfis dos Usuários",
            },
        ),
        migrations.CreateModel(
            name="UsuarioEmpresa",
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
                    "role",
                    models.CharField(
                        choices=[
                            ("ADMIN", "Administrador"),
                            ("GERENTE", "Gerente"),
                            ("OPERADOR", "Operador"),
                            ("VIEWER", "Visualizador"),
                        ],
                        max_length=10,
                    ),
                ),
                ("ativo", models.BooleanField(default=True)),
                ("data_vinculo", models.DateTimeField(auto_now_add=True)),
                (
                    "empresa",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="core.empresa"
                    ),
                ),
                (
                    "usuario",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Usuário da Empresa",
                "verbose_name_plural": "Usuários das Empresas",
                "unique_together": {("usuario", "empresa")},
            },
        ),
    ]
