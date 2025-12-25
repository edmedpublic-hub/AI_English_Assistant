from django.apps import AppConfig

class VocabMasterConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "vocab_master"

    def ready(self):
        import vocab_master.signals