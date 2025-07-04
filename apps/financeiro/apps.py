from django.apps import AppConfig


class FinanceiroConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.financeiro"
    verbose_name = "Módulo Financeiro"

    def ready(self):
        # Importar signals se necessário
        try:
            import apps.financeiro.signals
        except ImportError:
            pass
