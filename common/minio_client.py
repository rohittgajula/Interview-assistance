"""
MinIO Client Utility for Interview Assistance Platform
Provides a centralized interface for all services to interact with MinIO object storage.
"""

import os
import io
from datetime import timedelta
from typing import Optional, BinaryIO, Union
from minio import Minio
from minio.error import S3Error
import logging

logger = logging.getLogger(__name__)


class MinIOClient:
    """
    Centralized MinIO client for file storage operations.
    
    Bucket Structure:
    - user-profiles: User profile images and avatars
    - user-documents: User uploaded documents
    - interview-audio: Interview audio files
    - interview-recordings: Full interview recordings
    - system-backups: System backup files
    - temporary-files: Temporary files (auto-cleanup)
    """
    
    def __init__(self):
        """Initialize MinIO client with environment variables."""
        self.endpoint = os.getenv('MINIO_ENDPOINT', 'minio:9000')
        self.access_key = os.getenv('MINIO_ROOT_USER', 'minioadmin')
        self.secret_key = os.getenv('MINIO_ROOT_PASSWORD', 'minioadmin')
        self.secure = os.getenv('MINIO_SECURE', 'False').lower() == 'true'
        
        try:
            self.client = Minio(
                self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure
            )
            logger.info(f"MinIO client initialized successfully: {self.endpoint}")
        except Exception as e:
            logger.error(f"Failed to initialize MinIO client: {str(e)}")
            raise
    
    def upload_file(
        self,
        bucket_name: str,
        object_name: str,
        file_data: Union[BinaryIO, bytes],
        content_type: str = 'application/octet-stream',
        metadata: Optional[dict] = None
    ) -> bool:
        """
        Upload a file to MinIO.
        
        Args:
            bucket_name: Name of the bucket
            object_name: Object name/path in the bucket
            file_data: File data as bytes or file-like object
            content_type: MIME type of the file
            metadata: Optional metadata dictionary
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert bytes to BytesIO if needed
            if isinstance(file_data, bytes):
                file_data = io.BytesIO(file_data)
                length = len(file_data.getvalue())
            else:
                # Get file size
                file_data.seek(0, 2)  # Seek to end
                length = file_data.tell()
                file_data.seek(0)  # Reset to beginning
            
            self.client.put_object(
                bucket_name,
                object_name,
                file_data,
                length,
                content_type=content_type,
                metadata=metadata or {}
            )
            logger.info(f"File uploaded successfully: {bucket_name}/{object_name}")
            return True
        except S3Error as e:
            logger.error(f"MinIO S3 error uploading file: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error uploading file: {str(e)}")
            return False
    
    def download_file(self, bucket_name: str, object_name: str) -> Optional[bytes]:
        """
        Download a file from MinIO.
        
        Args:
            bucket_name: Name of the bucket
            object_name: Object name/path in the bucket
            
        Returns:
            bytes: File data if successful, None otherwise
        """
        try:
            response = self.client.get_object(bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            logger.info(f"File downloaded successfully: {bucket_name}/{object_name}")
            return data
        except S3Error as e:
            logger.error(f"MinIO S3 error downloading file: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error downloading file: {str(e)}")
            return None
    
    def delete_file(self, bucket_name: str, object_name: str) -> bool:
        """
        Delete a file from MinIO.
        
        Args:
            bucket_name: Name of the bucket
            object_name: Object name/path in the bucket
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.client.remove_object(bucket_name, object_name)
            logger.info(f"File deleted successfully: {bucket_name}/{object_name}")
            return True
        except S3Error as e:
            logger.error(f"MinIO S3 error deleting file: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting file: {str(e)}")
            return False
    
    def get_presigned_url(
        self,
        bucket_name: str,
        object_name: str,
        expires: timedelta = timedelta(hours=1)
    ) -> Optional[str]:
        """
        Generate a presigned URL for temporary access to a file.
        
        Args:
            bucket_name: Name of the bucket
            object_name: Object name/path in the bucket
            expires: URL expiration time (default: 1 hour)
            
        Returns:
            str: Presigned URL if successful, None otherwise
        """
        try:
            url = self.client.presigned_get_object(bucket_name, object_name, expires)
            logger.info(f"Presigned URL generated for: {bucket_name}/{object_name}")
            return url
        except S3Error as e:
            logger.error(f"MinIO S3 error generating presigned URL: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error generating presigned URL: {str(e)}")
            return None
    
    def file_exists(self, bucket_name: str, object_name: str) -> bool:
        """
        Check if a file exists in MinIO.
        
        Args:
            bucket_name: Name of the bucket
            object_name: Object name/path in the bucket
            
        Returns:
            bool: True if file exists, False otherwise
        """
        try:
            self.client.stat_object(bucket_name, object_name)
            return True
        except S3Error:
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking file existence: {str(e)}")
            return False
    
    def list_files(self, bucket_name: str, prefix: str = "") -> list:
        """
        List files in a bucket with optional prefix filter.
        
        Args:
            bucket_name: Name of the bucket
            prefix: Prefix to filter objects (directory path)
            
        Returns:
            list: List of object names
        """
        try:
            objects = self.client.list_objects(bucket_name, prefix=prefix, recursive=True)
            file_list = [obj.object_name for obj in objects]
            logger.info(f"Listed {len(file_list)} files from {bucket_name}/{prefix}")
            return file_list
        except S3Error as e:
            logger.error(f"MinIO S3 error listing files: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error listing files: {str(e)}")
            return []


# Singleton instance
_minio_client = None


def get_minio_client() -> MinIOClient:
    """
    Get or create a singleton MinIO client instance.
    
    Returns:
        MinIOClient: Singleton MinIO client instance
    """
    global _minio_client
    if _minio_client is None:
        _minio_client = MinIOClient()
    return _minio_client
