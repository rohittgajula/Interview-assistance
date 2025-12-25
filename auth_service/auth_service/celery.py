import os
import sys
from celery import Celery
from django.conf import settings
from common.celery_config import beat_schedule, task_routes

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_service.settings')

# Add common directory to path for shared configuration (/app/common)
sys.path.insert(0, '/app/common')

app = Celery('auth_service')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Auto-discover tasks from common directory
app.autodiscover_tasks(['common'], related_name='log_backup_tasks')

# Apply shared configuration
app.conf.beat_schedule = beat_schedule
app.conf.task_routes = task_routes

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
