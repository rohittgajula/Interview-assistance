import os
import sys
from celery import Celery
from django.conf import settings
from common.celery_config import task_routes

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_service.settings')

# Add common directory to path for telemetry (/app/common)
sys.path.insert(0, '/app/common')

# Initialize OpenTelemetry for Celery workers ONLY if running as worker
# (The __init__.py handles telemetry for Django web service)
try:
    is_celery_worker = os.getenv('IS_CELERY_WORKER', 'false').lower() == 'true'

    if is_celery_worker:
        from telemetry import configure_opentelemetry
        from opentelemetry.instrumentation.celery import CeleryInstrumentor
        configure_opentelemetry(service_name='auth_celery_worker', service_version='1.0.0')
        CeleryInstrumentor().instrument()
except Exception as e:
    print(f"Warning: Failed to initialize OpenTelemetry for Celery: {e}")

app = Celery('auth_service')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Apply shared configuration
app.conf.task_routes = task_routes

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
