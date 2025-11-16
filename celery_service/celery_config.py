import os
import sys
from celery import Celery as CeleryApp

# Add service paths to Python path for task discovery
sys.path.insert(0, '/app/bloom_filter_service')
sys.path.insert(0, '/app/auth_service')
sys.path.insert(0, '/app/interview_service')

# Set the default Django settings module for celery beat scheduler
# Only used when running with django_celery_beat
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bloom_filter_service.settings')

app = CeleryApp('interview_assistance')

# Configure broker and backend from environment (don't use Django settings)
app.conf.broker_url = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
app.conf.result_backend = os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')

# Celery Beat Schedule Configuration
app.conf.beat_schedule = {
    'clear-bloom-filter-hourly': {
        'task': 'bloom_filter.tasks.clear_bloom_filter',
        'schedule': float(os.getenv('BLOOM_FILTER_CLEAR_INTERVAL', 3600)),  # Default: every hour
    },
}

# Task routing - send tasks to specific queues
app.conf.task_routes = {
    'bloom_filter.tasks.*': {'queue': 'bloom_filter_queue'},
    'auth_service.tasks.*': {'queue': 'auth_queue'},
    'interview_service.tasks.*': {'queue': 'interview_queue'},
}

# Additional Celery configurations
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Auto-discover tasks from all Django apps
# This will look for tasks.py in each app
app.autodiscover_tasks([
    'bloom_filter',
    # Add other apps here as needed
    # 'auth_service.users',
    # 'interview_service.interviews',
])

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
