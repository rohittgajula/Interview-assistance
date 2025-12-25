from .celery import app as celery_app
import sys

# Add common directory to path (/app/common)
sys.path.insert(0, '/app/common')

__all__ = ('celery_app',)
