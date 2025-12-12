from .celery import app as celery_app
import sys
import os

# Add common directory to path (/app/common)
sys.path.insert(0, '/app/common')

# Initialize OpenTelemetry only if not running as Celery worker
# (Celery workers initialize telemetry in celery.py with their own service name)
try:
    # Check if we're running as a Celery worker via environment variable
    is_celery_worker = os.getenv('IS_CELERY_WORKER', 'false').lower() == 'true'

    if not is_celery_worker:
        from telemetry import configure_opentelemetry
        configure_opentelemetry(service_name='interview_service', service_version='1.0.0')
except Exception as e:
    print(f"Warning: Failed to initialize OpenTelemetry: {e}")

__all__ = ('celery_app',)
