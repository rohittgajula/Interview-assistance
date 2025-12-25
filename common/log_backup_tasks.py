"""
Celery tasks for automatic log backup to MinIO.

These tasks are shared across all services and handle:
- Periodic backup of rotated log files
- Cleanup of old logs from MinIO
"""

import os
import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name='common.backup_logs')
def backup_logs_task(service_name: str, logs_dir: str = 'logs'):
    """
    Celery task to backup rotated log files to MinIO.

    Args:
        service_name: Name of the service (e.g., 'interview_service')
        logs_dir: Directory containing log files (default: 'logs')

    Returns:
        Number of files successfully backed up
    """
    try:
        from minio_log_backup import backup_service_logs

        logger.info(f"Starting log backup for {service_name}")
        count = backup_service_logs(service_name, logs_dir)
        logger.info(f"Completed log backup for {service_name}: {count} files backed up")
        return count

    except Exception as e:
        logger.error(f"Failed to backup logs for {service_name}: {e}", exc_info=True)
        raise


@shared_task(name='common.cleanup_old_logs')
def cleanup_old_logs_task(service_name: str, days_to_keep: int = 30):
    """
    Celery task to cleanup old logs from MinIO.

    Args:
        service_name: Name of the service
        days_to_keep: Number of days to retain logs (default: 30)

    Returns:
        Number of files deleted
    """
    try:
        from minio_log_backup import get_minio_client, MinioLogBackup

        logger.info(f"Starting log cleanup for {service_name}, keeping last {days_to_keep} days")

        client = get_minio_client()
        backup_handler = MinioLogBackup(client)
        count = backup_handler.cleanup_old_logs(service_name, days_to_keep)

        logger.info(f"Completed log cleanup for {service_name}: {count} files deleted")
        return count

    except Exception as e:
        logger.error(f"Failed to cleanup old logs for {service_name}: {e}", exc_info=True)
        raise
