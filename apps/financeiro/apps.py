from django.apps import AppConfig


class FinanceiroConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.financeiro"
    verbose_name = "Módulo Financeiro"

    def ready(self):
        """
        Importa os signals quando a aplicação está pronta.
        """
        import apps.financeiro.signals
