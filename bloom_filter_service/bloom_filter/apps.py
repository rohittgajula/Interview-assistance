from django.apps import AppConfig


class BloomFilterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bloom_filter'

    def ready(self) -> None:
        from . import signals
        


