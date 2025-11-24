import os
from celery import Celery
from django.conf import settings
from common.celery_config import task_routes

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_service.settings')

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
