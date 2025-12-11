from django.apps import AppConfig
import sys
import os


class BloomFilterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bloom_filter'

    def ready(self) -> None:
        from . import signals
        


