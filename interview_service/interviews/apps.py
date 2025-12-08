from django.apps import AppConfig
import sys
import os


class InterviewsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'interviews'

    def ready(self):
        """
        Called when Django has initialized.
        This is the right place to instrument Django with OpenTelemetry.
        """
        # Add the parent directory to sys.path to allow importing common modules
        parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        if parent_dir not in sys.path:
            sys.path.append(parent_dir)

        # Instrument Django after it's fully initialized
        from common.tracing import instrument_django_tracing
        instrument_django_tracing()
