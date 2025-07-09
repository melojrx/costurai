from django.apps import AppConfig


class CadastrosConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.cadastros"
    verbose_name = "Cadastros - Clientes, Fornecedores e Produtos"

    def ready(self):
        """
        Importa os signals quando a aplicação está pronta.
        """
        import apps.cadastros.signals
