from django.apps import AppConfig
import sys
import os


class InterviewsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'interviews'

    def ready(self):
        """
        Called when Django has initialized.
        """
        pass
