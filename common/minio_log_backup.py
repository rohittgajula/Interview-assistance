"""
MinIO Log Backup Utility

This module provides functionality to backup rotated log files to MinIO object storage.
This prevents log files from accumulating on disk and slowing down the server.
"""

import os
import logging
import gzip
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class MinioLogBackup:
    """
    Handles backing up log files to MinIO object storage.

    Features:
    - Compresses log files before upload
    - Organizes logs by service and date
    - Cleans up local files after successful upload
    - Maintains retention policy
    """

    def __init__(self, minio_client, bucket_name: str = 'service-logs'):
        """
        Initialize the MinIO log backup handler.

        Args:
            minio_client: MinIO client instance
            bucket_name: Name of the bucket to store logs (default: 'service-logs')
        """
        self.client = minio_client
        self.bucket_name = bucket_name
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Create the logs bucket if it doesn't exist."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created MinIO bucket: {self.bucket_name}")
            else:
                logger.debug(f"MinIO bucket already exists: {self.bucket_name}")
        except Exception as e:
            logger.error(f"Failed to create/check MinIO bucket {self.bucket_name}: {e}")
            raise

    def compress_file(self, file_path: Path) -> Path:
        """
        Compress a log file using gzip.

        Args:
            file_path: Path to the log file to compress

        Returns:
            Path to the compressed file
        """
        compressed_path = file_path.with_suffix(file_path.suffix + '.gz')

        try:
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb', compresslevel=9) as f_out:
                    f_out.writelines(f_in)

            logger.info(f"Compressed {file_path} to {compressed_path}")
            return compressed_path
        except Exception as e:
            logger.error(f"Failed to compress {file_path}: {e}")
            raise

    def upload_log_file(self, file_path: Path, service_name: str,
                       compress: bool = True, delete_after_upload: bool = True) -> bool:
        """
        Upload a log file to MinIO.

        Args:
            file_path: Path to the log file
            service_name: Name of the service (for organizing in MinIO)
            compress: Whether to compress the file before upload (default: True)
            delete_after_upload: Whether to delete the local file after successful upload

        Returns:
            True if upload was successful, False otherwise
        """
        if not file_path.exists():
            logger.warning(f"Log file does not exist: {file_path}")
            return False

        try:
            # Compress the file if requested
            upload_file = file_path
            if compress and not str(file_path).endswith('.gz'):
                upload_file = self.compress_file(file_path)

            # Create object name with service name and timestamp
            timestamp = datetime.now().strftime('%Y/%m/%d')
            file_name = upload_file.name
            object_name = f"{service_name}/{timestamp}/{file_name}"

            # Upload to MinIO
            self.client.fput_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                file_path=str(upload_file)
            )

            logger.info(f"Uploaded {upload_file} to MinIO: {object_name}")

            # Clean up local files
            if delete_after_upload:
                try:
                    upload_file.unlink()
                    logger.info(f"Deleted local file: {upload_file}")

                    # If we compressed, also delete the original
                    if compress and upload_file != file_path:
                        file_path.unlink()
                        logger.info(f"Deleted original file: {file_path}")
                except Exception as e:
                    logger.error(f"Failed to delete local file {upload_file}: {e}")

            return True

        except Exception as e:
            logger.error(f"Failed to upload {file_path} to MinIO: {e}")
            # Clean up compressed file if it was created
            if compress and upload_file != file_path and upload_file.exists():
                try:
                    upload_file.unlink()
                except:
                    pass
            return False

    def backup_rotated_logs(self, logs_dir: str, service_name: str,
                           pattern: str = "*.log.*") -> int:
        """
        Backup all rotated log files in a directory.

        Rotated log files typically have extensions like .log.1, .log.2, etc.

        Args:
            logs_dir: Directory containing log files
            service_name: Name of the service
            pattern: Glob pattern to match rotated log files (default: "*.log.*")

        Returns:
            Number of files successfully backed up
        """
        logs_path = Path(logs_dir)
        if not logs_path.exists():
            logger.warning(f"Logs directory does not exist: {logs_dir}")
            return 0

        rotated_files = list(logs_path.glob(pattern))
        if not rotated_files:
            logger.info(f"No rotated log files found in {logs_dir}")
            return 0

        logger.info(f"Found {len(rotated_files)} rotated log files in {logs_dir}")

        success_count = 0
        for log_file in rotated_files:
            if self.upload_log_file(log_file, service_name):
                success_count += 1

        logger.info(f"Successfully backed up {success_count}/{len(rotated_files)} log files")
        return success_count

    def cleanup_old_logs(self, service_name: str, days_to_keep: int = 30) -> int:
        """
        Delete log files older than specified days from MinIO.

        Args:
            service_name: Name of the service
            days_to_keep: Number of days to retain logs (default: 30)

        Returns:
            Number of files deleted
        """
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        deleted_count = 0

        try:
            # List all objects for this service
            objects = self.client.list_objects(
                self.bucket_name,
                prefix=f"{service_name}/",
                recursive=True
            )

            for obj in objects:
                # Check if object is older than cutoff date
                if obj.last_modified < cutoff_date:
                    self.client.remove_object(self.bucket_name, obj.object_name)
                    deleted_count += 1
                    logger.info(f"Deleted old log from MinIO: {obj.object_name}")

            logger.info(f"Cleaned up {deleted_count} old log files for {service_name}")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup old logs for {service_name}: {e}")
            return deleted_count


def get_minio_client():
    """
    Get a MinIO client instance using environment variables.

    Returns:
        MinIO client instance
    """
    from minio import Minio

    endpoint = os.getenv('MINIO_ENDPOINT', 'minio:9000')
    access_key = os.getenv('MINIO_ROOT_USER', 'minioadmin')
    secret_key = os.getenv('MINIO_ROOT_PASSWORD', 'minioadmin')
    secure = os.getenv('MINIO_SECURE', 'False') == 'True'

    return Minio(
        endpoint,
        access_key=access_key,
        secret_key=secret_key,
        secure=secure
    )


def backup_service_logs(service_name: str, logs_dir: str = 'logs') -> int:
    """
    Convenience function to backup logs for a service.

    Args:
        service_name: Name of the service
        logs_dir: Directory containing log files (default: 'logs')

    Returns:
        Number of files successfully backed up
    """
    try:
        client = get_minio_client()
        backup_handler = MinioLogBackup(client)
        return backup_handler.backup_rotated_logs(logs_dir, service_name)
    except Exception as e:
        logger.error(f"Failed to backup logs for {service_name}: {e}")
        return 0
