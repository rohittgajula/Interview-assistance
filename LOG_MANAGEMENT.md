# Log Management System

This document describes the automated log management system for backing up application logs to MinIO object storage.

## Overview

The log management system automatically:
- Backs up rotated log files to MinIO object storage
- Compresses logs before upload to save storage space
- Organizes logs by service and date
- Cleans up old logs based on retention policy
- Prevents log files from accumulating and slowing down servers

## Architecture

### Components

1. **Logging Configuration** ([common/logging_config.py](common/logging_config.py))
   - Configures Python logging with RotatingFileHandler
   - Rotates logs when they reach 15MB
   - Keeps up to 10 backup files locally
   - Silences DEBUG logs from Daphne/Django server

2. **MinIO Log Backup Utility** ([common/minio_log_backup.py](common/minio_log_backup.py))
   - Handles uploading log files to MinIO
   - Compresses logs using gzip (compression level 9)
   - Organizes logs by service and date
   - Cleans up local files after successful upload

3. **Celery Tasks** ([common/log_backup_tasks.py](common/log_backup_tasks.py))
   - `common.backup_logs`: Backs up rotated logs to MinIO
   - `common.cleanup_old_logs`: Removes old logs from MinIO

4. **Scheduled Tasks** ([common/celery_config.py](common/celery_config.py))
   - Daily backups at 2 AM for each service
   - Weekly cleanup on Sundays at 3 AM

## How It Works

### Automatic Log Rotation

1. Application writes logs to `logs/{service_name}.log`
2. When log file reaches 15MB, it's rotated to `{service_name}.log.1`
3. Previous rotated logs are renamed (`.1` → `.2`, `.2` → `.3`, etc.)
4. Old rotated logs beyond the 10-file limit are deleted

### Automatic Backup to MinIO

Celery Beat schedules daily backups:

```
- 2:00 AM - auth_service logs backup
- 2:15 AM - interview_service logs backup
- 2:30 AM - bloom_filter_service logs backup
```

For each backup:
1. Celery task finds all rotated log files (e.g., `*.log.*`)
2. Each log file is compressed using gzip
3. Compressed files are uploaded to MinIO bucket `service-logs`
4. Files are organized: `{service_name}/{YYYY}/{MM}/{DD}/{filename}.gz`
5. Local files (both original and compressed) are deleted after successful upload

### Log Cleanup

Every Sunday at 3 AM:
- Task scans MinIO `service-logs` bucket
- Deletes log files older than retention period (default: 30 days)
- Configurable via `LOG_RETENTION_DAYS` environment variable

## Configuration

### Environment Variables

```bash
# MinIO Configuration (already set for services)
MINIO_ENDPOINT=minio:9000
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
MINIO_SECURE=False

# Log Retention (optional)
LOG_RETENTION_DAYS=30  # Default: 30 days
```

### Logging Levels

Each service uses the logging configuration from `common/logging_config.py`:

```python
# In settings.py
from logging_config import get_logging_config
LOGGING = get_logging_config('service_name', log_level='DEBUG' if DEBUG else 'INFO')
```

**Logging Levels:**
- `DEBUG=True` (development): DEBUG level - very verbose
- `DEBUG=False` (production): INFO level - normal verbosity

**Silenced Loggers:**
- `daphne`: INFO level (silences HTTP request/response DEBUG logs)
- `django.server`: INFO level (silences server DEBUG logs)
- `asyncio`: WARNING level (silences event loop DEBUG logs)

### Disable DEBUG Logs

To disable the DEBUG logs you're seeing in development:

**Option 1: Set log level to INFO in settings**

```python
# In interview_service/settings.py (or other service)
LOGGING = get_logging_config('interview_service', log_level='INFO')
```

**Option 2: Set DEBUG=False**

```python
# In settings.py
DEBUG = False
```

This will automatically use INFO level logging.

## Manual Operations

### Manually Backup Logs

You can manually trigger a log backup using Celery:

```bash
# From within a container or with celery CLI
celery -A auth_service call common.backup_logs --args='["auth_service", "logs"]'
```

Or use the Python API:

```python
from common.minio_log_backup import backup_service_logs

# Backup logs for a service
count = backup_service_logs('auth_service', 'logs')
print(f"Backed up {count} log files")
```

### Manually Cleanup Old Logs

```bash
# From within a container or with celery CLI
celery -A auth_service call common.cleanup_old_logs --args='["auth_service"]' --kwargs='{"days_to_keep": 30}'
```

Or use the Python API:

```python
from common.minio_log_backup import get_minio_client, MinioLogBackup

client = get_minio_client()
backup = MinioLogBackup(client)
count = backup.cleanup_old_logs('auth_service', days_to_keep=30)
print(f"Deleted {count} old log files")
```

## MinIO Structure

Logs are stored in the `service-logs` bucket with the following structure:

```
service-logs/
├── auth_service/
│   ├── 2025/
│   │   ├── 12/
│   │   │   ├── 20/
│   │   │   │   ├── auth_service.log.1.gz
│   │   │   │   ├── auth_service.log.2.gz
│   │   │   │   └── ...
├── interview_service/
│   ├── 2025/
│   │   ├── 12/
│   │   │   ├── 20/
│   │   │   │   ├── interview_service.log.1.gz
│   │   │   │   └── ...
├── bloom_filter_service/
│   └── ...
```

## Accessing Logs

### View Logs in MinIO Console

1. Open MinIO Console: http://localhost:9001
2. Login with credentials (default: minioadmin/minioadmin)
3. Navigate to `service-logs` bucket
4. Browse by service and date
5. Download and decompress files to view

### Download and View Logs

```bash
# Using MinIO client (mc)
mc alias set myminio http://localhost:9000 minioadmin minioadmin
mc ls myminio/service-logs/auth_service/
mc cp myminio/service-logs/auth_service/2025/12/20/auth_service.log.1.gz .

# Decompress and view
gunzip auth_service.log.1.gz
cat auth_service.log.1
```

### Search Logs

```bash
# Download all logs for a service and search
mc mirror myminio/service-logs/auth_service/ ./auth_logs/
zgrep "ERROR" ./auth_logs/**/*.gz
```

## Celery Beat Schedule

The complete Celery Beat schedule (from [common/celery_config.py](common/celery_config.py)):

```python
beat_schedule = {
    # Bloom filter maintenance
    'clear-bloom-filter-hourly': {
        'task': 'bloom_filter.tasks.clear_bloom_filter',
        'schedule': 3600,  # Every hour
    },

    # Log backups (daily at 2 AM)
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

    # Log cleanup (weekly on Sundays at 3 AM)
    'cleanup-old-logs': {
        'task': 'common.cleanup_old_logs',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),
        'kwargs': {'days_to_keep': 30},
    },
}
```

## Docker Configuration

The `maintenance_celery_worker` container in [docker-compose.yml](docker-compose.yml) handles log backup tasks:

```yaml
maintenance_celery_worker:
  build:
    context: ./auth_service
  container_name: maintenance_celery_worker
  volumes:
    - ./auth_service:/app
    - ./auth_service/logs:/app/logs
    - ./interview_service/logs:/app/interview_logs
    - ./bloom_filter_service/logs:/app/bloom_logs
    - ./common:/app/common
  command: celery -A auth_service worker --loglevel=info --queues=maintenance_queue
  depends_on:
    - redis
    - minio
```

This worker:
- Has access to all service log directories
- Listens to the `maintenance_queue`
- Depends on Redis (for Celery) and MinIO (for uploads)

## Troubleshooting

### Logs Not Being Backed Up

1. Check if Celery Beat is running:
   ```bash
   docker logs celery_beat
   ```

2. Check if maintenance worker is running:
   ```bash
   docker logs maintenance_celery_worker
   ```

3. Check Celery Flower for task status:
   - Open http://localhost:5555
   - Look for `common.backup_logs` tasks

4. Manually trigger a backup to test:
   ```bash
   docker exec -it maintenance_celery_worker celery -A auth_service call common.backup_logs --args='["auth_service", "logs"]'
   ```

### MinIO Connection Issues

1. Check MinIO is running:
   ```bash
   docker ps | grep minio
   ```

2. Check MinIO health:
   ```bash
   curl http://localhost:9000/minio/health/live
   ```

3. Verify bucket exists:
   ```bash
   docker exec -it minio-client mc ls myminio/service-logs
   ```

### No Rotated Logs Found

This is normal if:
- Service hasn't generated 15MB of logs yet
- Logs were recently backed up and deleted
- Service just started

To test the system, you can manually create a test log file:

```bash
# In the service container
touch logs/test_service.log.1
```

Then trigger a backup manually to verify the system works.

## Best Practices

1. **Monitor Disk Space**: Even with automatic backups, monitor disk usage
2. **Adjust Retention**: Set `LOG_RETENTION_DAYS` based on compliance requirements
3. **Regular Backups**: Keep the 2 AM schedule for off-peak backup
4. **MinIO Backups**: Consider backing up the MinIO `service-logs` bucket itself
5. **Log Levels**: Use INFO in production, DEBUG only when troubleshooting

## Security Considerations

1. **Access Control**: Logs may contain sensitive information
   - MinIO bucket is not publicly accessible
   - Only services and maintenance worker can access

2. **Retention Policy**: Balance storage costs with compliance needs
   - Default 30 days may not meet compliance requirements
   - Adjust `LOG_RETENTION_DAYS` as needed

3. **Compression**: All uploaded logs are compressed
   - Saves storage space
   - Adds slight overhead to viewing logs
