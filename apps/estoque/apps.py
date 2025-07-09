from django.apps import AppConfig


class EstoqueConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.estoque"

    def ready(self):
        """
        Importa os signals quando a aplicação está pronta.
        """
        import apps.estoque.signals
