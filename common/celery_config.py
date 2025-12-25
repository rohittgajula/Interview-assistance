import os
from celery.schedules import crontab

# Celery Beat Schedule Configuration
beat_schedule = {
    'clear-bloom-filter-hourly': {
        'task': 'bloom_filter.tasks.clear_bloom_filter',
        'schedule': float(os.getenv('BLOOM_FILTER_CLEAR_INTERVAL', 3600)),  # Default: every hour
    },
    # Backup logs daily at 2 AM for all services
    'backup-auth-service-logs': {
        'task': 'common.backup_logs',
        'schedule': crontab(hour=2, minute=0),
        'args': ('auth_service', 'logs'),
    },
    'backup-interview-service-logs': {
        'task': 'common.backup_logs',
        'schedule': crontab(hour=2, minute=15),
        'args': ('interview_service', 'logs'),
    },
    'backup-bloom-filter-service-logs': {
        'task': 'common.backup_logs',
        'schedule': crontab(hour=2, minute=30),
        'args': ('bloom_filter_service', 'logs'),
    },
    # Cleanup old logs weekly (every Sunday at 3 AM)
    'cleanup-old-logs': {
        'task': 'common.cleanup_old_logs',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),  # Sunday
        'kwargs': {'days_to_keep': int(os.getenv('LOG_RETENTION_DAYS', 30))},
    },
}

# Task routing - send tasks to specific queues
task_routes = {
    'bloom_filter.tasks.*': {'queue': 'bloom_filter_queue'},
    'auth_service.tasks.*': {'queue': 'auth_queue'},
    'interview_service.tasks.*': {'queue': 'interview_queue'},
    'common.backup_logs': {'queue': 'maintenance_queue'},
    'common.cleanup_old_logs': {'queue': 'maintenance_queue'},
}
