from django.apps import AppConfig


class ProducaoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.producao"
    verbose_name = "Produção - Ordens de Produção"
    
    def ready(self):
        """Importar signals quando o app estiver pronto"""
        import apps.producao.signals