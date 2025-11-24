import os

# Celery Beat Schedule Configuration
beat_schedule = {
    'clear-bloom-filter-hourly': {
        'task': 'bloom_filter.tasks.clear_bloom_filter',
        'schedule': float(os.getenv('BLOOM_FILTER_CLEAR_INTERVAL', 3600)),  # Default: every hour
    },
}

# Task routing - send tasks to specific queues
task_routes = {
    'bloom_filter.tasks.*': {'queue': 'bloom_filter_queue'},
    'auth_service.tasks.*': {'queue': 'auth_queue'},
    'interview_service.tasks.*': {'queue': 'interview_queue'},
}
