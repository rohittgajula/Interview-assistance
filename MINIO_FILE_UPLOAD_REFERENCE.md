# MinIO File Upload/Update/Delete - Complete Implementation Reference

## Overview
This document provides complete, ready-to-use code for uploading, updating, and deleting files (avatars, resumes, documents) to MinIO buckets with versioning support, JWT authentication, and validation.

---

## 1. File Upload Utilities (`common/file_utils.py`)

**Create this new file** with reusable validation and helper functions:

```python
"""
File Upload Utilities for MinIO Integration
Provides validation, filename generation, and URL parsing helpers
"""

import os
import re
import mimetypes
from datetime import datetime
from typing import Optional, Tuple
from django.core.exceptions import ValidationError
from django.conf import settings


# File size limits (in bytes)
MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5MB
MAX_RESUME_SIZE = 2 * 1024 * 1024  # 2MB
MAX_DOCUMENT_SIZE = 10 * 1024 * 1024  # 10MB

# Allowed MIME types
ALLOWED_AVATAR_TYPES = ['image/jpeg', 'image/png', 'image/gif']
ALLOWED_RESUME_TYPES = ['application/pdf']
ALLOWED_DOCUMENT_TYPES = ['application/pdf', 'application/msword',
                          'application/vnd.openxmlformats-officedocument.wordprocessingml.document']


def validate_file_size(file, max_size_bytes: int, file_type: str = "File"):
    """
    Validate that file size doesn't exceed the maximum allowed.

    Args:
        file: Django UploadedFile object
        max_size_bytes: Maximum allowed size in bytes
        file_type: Type of file for error message (e.g., "Avatar", "Resume")

    Raises:
        ValidationError: If file size exceeds limit
    """
    if file.size > max_size_bytes:
        max_size_mb = max_size_bytes / (1024 * 1024)
        raise ValidationError(
            f"{file_type} size ({file.size / (1024 * 1024):.2f}MB) exceeds "
            f"maximum allowed size ({max_size_mb:.0f}MB)"
        )


def validate_file_type(file, allowed_types: list, file_type: str = "File"):
    """
    Validate that file MIME type is in the allowed list.

    Args:
        file: Django UploadedFile object
        allowed_types: List of allowed MIME types
        file_type: Type of file for error message

    Raises:
        ValidationError: If file type is not allowed
    """
    # Check content_type from upload
    if file.content_type not in allowed_types:
        raise ValidationError(
            f"{file_type} type '{file.content_type}' is not allowed. "
            f"Allowed types: {', '.join(allowed_types)}"
        )

    # Additional check using mimetypes based on file extension
    guessed_type, _ = mimetypes.guess_type(file.name)
    if guessed_type and guessed_type not in allowed_types:
        raise ValidationError(
            f"{file_type} extension does not match an allowed type. "
            f"Allowed types: {', '.join(allowed_types)}"
        )


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal and special characters.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename safe for storage
    """
    # Get base name without path
    filename = os.path.basename(filename)

    # Remove or replace special characters, keep only alphanumeric, dots, dashes, underscores
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)

    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')

    # Limit length to 100 characters
    name, ext = os.path.splitext(filename)
    if len(name) > 100:
        name = name[:100]

    return f"{name}{ext}"


def generate_versioned_filename(user_id: int, file_type: str, original_filename: str) -> str:
    """
    Generate a versioned filename with timestamp for MinIO storage.

    Args:
        user_id: User's ID
        file_type: Type of file ('avatar', 'resume', 'document')
        original_filename: Original uploaded filename

    Returns:
        Full object path in MinIO (e.g., 'avatars/123/2025-12-19_153000_photo.jpg')
    """
    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
    sanitized = sanitize_filename(original_filename)

    # Map file types to directory names
    type_dirs = {
        'avatar': 'avatars',
        'resume': 'resumes',
        'document': 'documents'
    }

    dir_name = type_dirs.get(file_type, 'files')

    return f"{dir_name}/{user_id}/{timestamp}_{sanitized}"


def parse_minio_url(file_url: str) -> Optional[Tuple[str, str]]:
    """
    Parse MinIO URL to extract bucket name and object name.

    Args:
        file_url: Full MinIO URL or relative path

    Returns:
        Tuple of (bucket_name, object_name) or None if parsing fails

    Examples:
        'http://minio:9000/user-profiles/avatars/123/file.jpg'
        -> ('user-profiles', 'avatars/123/file.jpg')

        '/user-profiles/avatars/123/file.jpg'
        -> ('user-profiles', 'avatars/123/file.jpg')
    """
    if not file_url:
        return None

    try:
        # Remove protocol and domain if present
        if '://' in file_url:
            file_url = file_url.split('://', 1)[1]
            # Remove host:port
            if '/' in file_url:
                file_url = file_url.split('/', 1)[1]

        # Remove leading slash
        file_url = file_url.lstrip('/')

        # Split into bucket and object path
        parts = file_url.split('/', 1)
        if len(parts) == 2:
            return parts[0], parts[1]

        return None
    except Exception:
        return None


def build_minio_url(bucket_name: str, object_name: str) -> str:
    """
    Build a MinIO URL from bucket and object name.

    Args:
        bucket_name: MinIO bucket name
        object_name: Object path in bucket

    Returns:
        Full MinIO URL
    """
    endpoint = getattr(settings, 'MINIO_ENDPOINT', 'minio:9000')
    secure = getattr(settings, 'MINIO_SECURE', False)
    protocol = 'https' if secure else 'http'

    return f"{protocol}://{endpoint}/{bucket_name}/{object_name}"


def validate_avatar(file):
    """
    Complete validation for avatar uploads.

    Args:
        file: Django UploadedFile object

    Raises:
        ValidationError: If validation fails
    """
    validate_file_size(file, MAX_AVATAR_SIZE, "Avatar")
    validate_file_type(file, ALLOWED_AVATAR_TYPES, "Avatar")


def validate_resume(file):
    """
    Complete validation for resume uploads.

    Args:
        file: Django UploadedFile object

    Raises:
        ValidationError: If validation fails
    """
    validate_file_size(file, MAX_RESUME_SIZE, "Resume")
    validate_file_type(file, ALLOWED_RESUME_TYPES, "Resume")


def validate_document(file):
    """
    Complete validation for general document uploads.

    Args:
        file: Django UploadedFile object

    Raises:
        ValidationError: If validation fails
    """
    validate_file_size(file, MAX_DOCUMENT_SIZE, "Document")
    validate_file_type(file, ALLOWED_DOCUMENT_TYPES, "Document")
```

---

## 2. Upload Serializers (`interview_service/interviews/serializers.py`)

**Add these serializers** to your existing serializers file:

```python
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
import sys
sys.path.append('/app')
from common.file_utils import validate_avatar, validate_resume


class AvatarUploadSerializer(serializers.Serializer):
    """
    Serializer for avatar image uploads.
    Validates file size (max 5MB) and type (JPEG, PNG, GIF).
    """
    avatar = serializers.ImageField(required=True)

    def validate_avatar(self, value):
        """
        Validate the uploaded avatar file.

        Args:
            value: Uploaded file

        Returns:
            Validated file

        Raises:
            serializers.ValidationError: If validation fails
        """
        try:
            validate_avatar(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e))

        return value


class ResumeUploadSerializer(serializers.Serializer):
    """
    Serializer for resume PDF uploads.
    Validates file size (max 2MB) and type (PDF only).
    """
    resume = serializers.FileField(required=True)

    def validate_resume(self, value):
        """
        Validate the uploaded resume file.

        Args:
            value: Uploaded file

        Returns:
            Validated file

        Raises:
            serializers.ValidationError: If validation fails
        """
        try:
            validate_resume(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e))

        return value


class FileDeleteSerializer(serializers.Serializer):
    """
    Serializer for file deletion confirmation.
    Used to validate delete requests.
    """
    file_type = serializers.ChoiceField(
        choices=['avatar', 'resume'],
        required=False,
        help_text="Type of file to delete"
    )
```

---

## 3. File Management Views (`interview_service/interviews/views.py`)

**Add these views** to your existing views file:

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .permissions import IsAuthenticated as CustomIsAuthenticated
from .models import UserProfile
from .serializers import (
    AvatarUploadSerializer,
    ResumeUploadSerializer,
    UserProfileSerializer
)
import sys
sys.path.append('/app')
from common.minio_client import get_minio_client
from common.file_utils import (
    generate_versioned_filename,
    parse_minio_url,
    build_minio_url
)
import logging

logger = logging.getLogger(__name__)


class AvatarUploadView(APIView):
    """
    API endpoint for uploading user avatar images.

    POST /api/v1/profiles/me/avatar/
    - Accepts multipart/form-data with 'avatar' field
    - Validates file size (max 5MB) and type (JPEG, PNG, GIF)
    - Stores file in MinIO 'user-profiles' bucket with versioning
    - Updates UserProfile.avatar_url

    Returns:
        200: Avatar uploaded successfully with new URL
        400: Validation error (file too large, wrong type, etc.)
        401: Unauthorized (no JWT token)
        404: User profile not found
        500: MinIO upload failure
    """
    permission_classes = [CustomIsAuthenticated]

    def post(self, request):
        user_id = request.user.id

        # Get user profile
        try:
            profile = UserProfile.objects.get(pk=user_id)
        except UserProfile.DoesNotExist:
            logger.error(f"Profile not found for user {user_id}")
            return Response({
                "error": "Profile not found."
            }, status=status.HTTP_404_NOT_FOUND)

        # Validate uploaded file
        serializer = AvatarUploadSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Avatar validation failed for user {user_id}: {serializer.errors}")
            return Response({
                "error": "Invalid file uploaded.",
                "details": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        avatar_file = serializer.validated_data['avatar']

        # Generate versioned filename
        object_name = generate_versioned_filename(
            user_id=user_id,
            file_type='avatar',
            original_filename=avatar_file.name
        )

        # Upload to MinIO
        minio_client = get_minio_client()
        bucket_name = 'user-profiles'

        try:
            success = minio_client.upload_file(
                bucket_name=bucket_name,
                object_name=object_name,
                file_data=avatar_file.read(),
                content_type=avatar_file.content_type,
                metadata={
                    'user_id': str(user_id),
                    'original_filename': avatar_file.name,
                    'file_type': 'avatar'
                }
            )

            if not success:
                logger.error(f"MinIO upload failed for user {user_id}")
                return Response({
                    "error": "Failed to upload file to storage."
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Build MinIO URL
            avatar_url = build_minio_url(bucket_name, object_name)

            # Update profile
            # Note: Old avatar file is NOT deleted (versioning enabled)
            profile.avatar_url = avatar_url
            profile.save(update_fields=['avatar_url'])

            logger.info(f"Avatar uploaded successfully for user {user_id}: {object_name}")

            return Response({
                "message": "Avatar uploaded successfully.",
                "avatar_url": avatar_url,
                "profile": UserProfileSerializer(profile).data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Unexpected error uploading avatar for user {user_id}: {str(e)}")
            return Response({
                "error": "An unexpected error occurred during upload."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ResumeUploadView(APIView):
    """
    API endpoint for uploading user resume PDFs.

    POST /api/v1/profiles/me/resume/
    - Accepts multipart/form-data with 'resume' field
    - Validates file size (max 2MB) and type (PDF only)
    - Stores file in MinIO 'user-documents' bucket with versioning
    - Updates UserProfile.resume_url

    Returns:
        200: Resume uploaded successfully with new URL
        400: Validation error
        401: Unauthorized
        404: User profile not found
        500: MinIO upload failure
    """
    permission_classes = [CustomIsAuthenticated]

    def post(self, request):
        user_id = request.user.id

        # Get user profile
        try:
            profile = UserProfile.objects.get(pk=user_id)
        except UserProfile.DoesNotExist:
            logger.error(f"Profile not found for user {user_id}")
            return Response({
                "error": "Profile not found."
            }, status=status.HTTP_404_NOT_FOUND)

        # Validate uploaded file
        serializer = ResumeUploadSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Resume validation failed for user {user_id}: {serializer.errors}")
            return Response({
                "error": "Invalid file uploaded.",
                "details": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        resume_file = serializer.validated_data['resume']

        # Generate versioned filename
        object_name = generate_versioned_filename(
            user_id=user_id,
            file_type='resume',
            original_filename=resume_file.name
        )

        # Upload to MinIO
        minio_client = get_minio_client()
        bucket_name = 'user-documents'

        try:
            success = minio_client.upload_file(
                bucket_name=bucket_name,
                object_name=object_name,
                file_data=resume_file.read(),
                content_type=resume_file.content_type,
                metadata={
                    'user_id': str(user_id),
                    'original_filename': resume_file.name,
                    'file_type': 'resume'
                }
            )

            if not success:
                logger.error(f"MinIO upload failed for user {user_id}")
                return Response({
                    "error": "Failed to upload file to storage."
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Build MinIO URL
            resume_url = build_minio_url(bucket_name, object_name)

            # Update profile (old resume file is NOT deleted - versioning enabled)
            profile.resume_url = resume_url
            profile.save(update_fields=['resume_url'])

            logger.info(f"Resume uploaded successfully for user {user_id}: {object_name}")

            return Response({
                "message": "Resume uploaded successfully.",
                "resume_url": resume_url,
                "profile": UserProfileSerializer(profile).data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Unexpected error uploading resume for user {user_id}: {str(e)}")
            return Response({
                "error": "An unexpected error occurred during upload."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AvatarDeleteView(APIView):
    """
    API endpoint for deleting user avatar.

    DELETE /api/v1/profiles/me/avatar/
    - Deletes current avatar file from MinIO
    - Clears UserProfile.avatar_url
    - Note: Only deletes current version, old versions remain in storage

    Returns:
        200: Avatar deleted successfully
        401: Unauthorized
        404: Profile or file not found
        500: MinIO deletion failure
    """
    permission_classes = [CustomIsAuthenticated]

    def delete(self, request):
        user_id = request.user.id

        # Get user profile
        try:
            profile = UserProfile.objects.get(pk=user_id)
        except UserProfile.DoesNotExist:
            logger.error(f"Profile not found for user {user_id}")
            return Response({
                "error": "Profile not found."
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if avatar exists
        if not profile.avatar_url:
            return Response({
                "error": "No avatar found to delete."
            }, status=status.HTTP_404_NOT_FOUND)

        # Parse MinIO URL to get bucket and object name
        parsed = parse_minio_url(profile.avatar_url)
        if not parsed:
            logger.error(f"Failed to parse avatar URL for user {user_id}: {profile.avatar_url}")
            return Response({
                "error": "Invalid avatar URL format."
            }, status=status.HTTP_400_BAD_REQUEST)

        bucket_name, object_name = parsed

        # Delete from MinIO
        minio_client = get_minio_client()

        try:
            # Check if file exists
            if not minio_client.file_exists(bucket_name, object_name):
                logger.warning(f"Avatar file not found in MinIO for user {user_id}: {object_name}")
                # Clear the URL even if file doesn't exist
                profile.avatar_url = ''
                profile.save(update_fields=['avatar_url'])
                return Response({
                    "message": "Avatar reference cleared (file not found in storage)."
                }, status=status.HTTP_200_OK)

            # Delete the file
            success = minio_client.delete_file(bucket_name, object_name)

            if not success:
                logger.error(f"MinIO deletion failed for user {user_id}: {object_name}")
                return Response({
                    "error": "Failed to delete file from storage."
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Clear avatar URL
            profile.avatar_url = ''
            profile.save(update_fields=['avatar_url'])

            logger.info(f"Avatar deleted successfully for user {user_id}: {object_name}")

            return Response({
                "message": "Avatar deleted successfully.",
                "profile": UserProfileSerializer(profile).data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Unexpected error deleting avatar for user {user_id}: {str(e)}")
            return Response({
                "error": "An unexpected error occurred during deletion."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ResumeDeleteView(APIView):
    """
    API endpoint for deleting user resume.

    DELETE /api/v1/profiles/me/resume/
    - Deletes current resume file from MinIO
    - Clears UserProfile.resume_url
    - Note: Only deletes current version, old versions remain in storage

    Returns:
        200: Resume deleted successfully
        401: Unauthorized
        404: Profile or file not found
        500: MinIO deletion failure
    """
    permission_classes = [CustomIsAuthenticated]

    def delete(self, request):
        user_id = request.user.id

        # Get user profile
        try:
            profile = UserProfile.objects.get(pk=user_id)
        except UserProfile.DoesNotExist:
            logger.error(f"Profile not found for user {user_id}")
            return Response({
                "error": "Profile not found."
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if resume exists
        if not profile.resume_url:
            return Response({
                "error": "No resume found to delete."
            }, status=status.HTTP_404_NOT_FOUND)

        # Parse MinIO URL
        parsed = parse_minio_url(profile.resume_url)
        if not parsed:
            logger.error(f"Failed to parse resume URL for user {user_id}: {profile.resume_url}")
            return Response({
                "error": "Invalid resume URL format."
            }, status=status.HTTP_400_BAD_REQUEST)

        bucket_name, object_name = parsed

        # Delete from MinIO
        minio_client = get_minio_client()

        try:
            # Check if file exists
            if not minio_client.file_exists(bucket_name, object_name):
                logger.warning(f"Resume file not found in MinIO for user {user_id}: {object_name}")
                # Clear the URL even if file doesn't exist
                profile.resume_url = ''
                profile.save(update_fields=['resume_url'])
                return Response({
                    "message": "Resume reference cleared (file not found in storage)."
                }, status=status.HTTP_200_OK)

            # Delete the file
            success = minio_client.delete_file(bucket_name, object_name)

            if not success:
                logger.error(f"MinIO deletion failed for user {user_id}: {object_name}")
                return Response({
                    "error": "Failed to delete file from storage."
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Clear resume URL
            profile.resume_url = ''
            profile.save(update_fields=['resume_url'])

            logger.info(f"Resume deleted successfully for user {user_id}: {object_name}")

            return Response({
                "message": "Resume deleted successfully.",
                "profile": UserProfileSerializer(profile).data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Unexpected error deleting resume for user {user_id}: {str(e)}")
            return Response({
                "error": "An unexpected error occurred during deletion."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FileVersionHistoryView(APIView):
    """
    BONUS: API endpoint to view file version history.

    GET /api/v1/profiles/me/files/history/?type=avatar|resume
    - Lists all versioned files for the authenticated user
    - Generates presigned URLs for download

    Query Parameters:
        type: 'avatar' or 'resume' (required)

    Returns:
        200: List of file versions with URLs and timestamps
        400: Invalid or missing type parameter
        401: Unauthorized
    """
    permission_classes = [CustomIsAuthenticated]

    def get(self, request):
        user_id = request.user.id
        file_type = request.query_params.get('type')

        if file_type not in ['avatar', 'resume']:
            return Response({
                "error": "Invalid file type. Must be 'avatar' or 'resume'."
            }, status=status.HTTP_400_BAD_REQUEST)

        # Map file types to bucket and prefix
        type_config = {
            'avatar': {
                'bucket': 'user-profiles',
                'prefix': f'avatars/{user_id}/'
            },
            'resume': {
                'bucket': 'user-documents',
                'prefix': f'resumes/{user_id}/'
            }
        }

        config = type_config[file_type]
        minio_client = get_minio_client()

        try:
            # List all files for this user and type
            file_list = minio_client.list_files(
                bucket_name=config['bucket'],
                prefix=config['prefix']
            )

            # Generate presigned URLs for each file
            from datetime import timedelta
            files_with_urls = []

            for object_name in file_list:
                # Extract filename and timestamp from path
                filename = os.path.basename(object_name)

                # Generate presigned URL (valid for 1 hour)
                url = minio_client.get_presigned_url(
                    bucket_name=config['bucket'],
                    object_name=object_name,
                    expires=timedelta(hours=1)
                )

                if url:
                    files_with_urls.append({
                        'filename': filename,
                        'object_name': object_name,
                        'download_url': url,
                        'expires_in': '1 hour'
                    })

            # Sort by filename (which includes timestamp) in descending order
            files_with_urls.sort(key=lambda x: x['filename'], reverse=True)

            return Response({
                "file_type": file_type,
                "total_versions": len(files_with_urls),
                "files": files_with_urls
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error listing file history for user {user_id}: {str(e)}")
            return Response({
                "error": "Failed to retrieve file history."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

---

## 4. URL Configuration (`interview_service/interviews/urls.py`)

**Add these URL patterns** to your existing urlpatterns:

```python
from django.urls import path
from . import views

urlpatterns = [
    # ... your existing patterns ...

    # File upload endpoints
    path("profiles/me/avatar/", views.AvatarUploadView.as_view(), name="avatar-upload"),
    path("profiles/me/resume/", views.ResumeUploadView.as_view(), name="resume-upload"),

    # File delete endpoints
    path("profiles/me/avatar/delete/", views.AvatarDeleteView.as_view(), name="avatar-delete"),
    path("profiles/me/resume/delete/", views.ResumeDeleteView.as_view(), name="resume-delete"),

    # Bonus: File version history
    path("profiles/me/files/history/", views.FileVersionHistoryView.as_view(), name="file-history"),
]
```

---

## 5. Complete Usage Examples

### 5.1 Python/Requests Examples

```python
import requests

# Your JWT token
TOKEN = "your_jwt_token_here"
BASE_URL = "http://localhost:8000/api/v1"

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

# ----- UPLOAD AVATAR -----
def upload_avatar(image_path):
    url = f"{BASE_URL}/profiles/me/avatar/"

    with open(image_path, 'rb') as f:
        files = {'avatar': f}
        response = requests.post(url, headers=headers, files=files)

    print(response.status_code)
    print(response.json())

# Usage
upload_avatar('/path/to/profile-photo.jpg')

# Expected Response:
# {
#   "message": "Avatar uploaded successfully.",
#   "avatar_url": "http://minio:9000/user-profiles/avatars/123/2025-12-19_153000_profile-photo.jpg",
#   "profile": { ... full profile data ... }
# }


# ----- UPLOAD RESUME -----
def upload_resume(pdf_path):
    url = f"{BASE_URL}/profiles/me/resume/"

    with open(pdf_path, 'rb') as f:
        files = {'resume': f}
        response = requests.post(url, headers=headers, files=files)

    print(response.status_code)
    print(response.json())

# Usage
upload_resume('/path/to/resume.pdf')


# ----- DELETE AVATAR -----
def delete_avatar():
    url = f"{BASE_URL}/profiles/me/avatar/delete/"
    response = requests.delete(url, headers=headers)

    print(response.status_code)
    print(response.json())

# Usage
delete_avatar()

# Expected Response:
# {
#   "message": "Avatar deleted successfully.",
#   "profile": { ... updated profile data ... }
# }


# ----- DELETE RESUME -----
def delete_resume():
    url = f"{BASE_URL}/profiles/me/resume/delete/"
    response = requests.delete(url, headers=headers)

    print(response.status_code)
    print(response.json())

# Usage
delete_resume()


# ----- VIEW FILE VERSION HISTORY -----
def view_avatar_history():
    url = f"{BASE_URL}/profiles/me/files/history/?type=avatar"
    response = requests.get(url, headers=headers)

    print(response.status_code)
    print(response.json())

# Usage
view_avatar_history()

# Expected Response:
# {
#   "file_type": "avatar",
#   "total_versions": 3,
#   "files": [
#     {
#       "filename": "2025-12-19_153000_new-avatar.jpg",
#       "object_name": "avatars/123/2025-12-19_153000_new-avatar.jpg",
#       "download_url": "http://minio:9000/user-profiles/avatars/123/...?X-Amz-...",
#       "expires_in": "1 hour"
#     },
#     {
#       "filename": "2025-12-19_103000_old-avatar.png",
#       "object_name": "avatars/123/2025-12-19_103000_old-avatar.png",
#       "download_url": "http://minio:9000/user-profiles/avatars/123/...?X-Amz-...",
#       "expires_in": "1 hour"
#     }
#   ]
# }
```

### 5.2 cURL Examples

```bash
# Get JWT token first (replace with your auth endpoint)
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}' \
  | jq -r '.access')

# ----- UPLOAD AVATAR -----
curl -X POST http://localhost:8000/api/v1/profiles/me/avatar/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "avatar=@/path/to/photo.jpg"

# Response:
# {
#   "message": "Avatar uploaded successfully.",
#   "avatar_url": "http://minio:9000/user-profiles/avatars/123/2025-12-19_153000_photo.jpg",
#   "profile": { ... }
# }


# ----- UPLOAD RESUME -----
curl -X POST http://localhost:8000/api/v1/profiles/me/resume/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "resume=@/path/to/resume.pdf"


# ----- DELETE AVATAR -----
curl -X DELETE http://localhost:8000/api/v1/profiles/me/avatar/delete/ \
  -H "Authorization: Bearer $TOKEN"


# ----- DELETE RESUME -----
curl -X DELETE http://localhost:8000/api/v1/profiles/me/resume/delete/ \
  -H "Authorization: Bearer $TOKEN"


# ----- VIEW AVATAR VERSION HISTORY -----
curl -X GET "http://localhost:8000/api/v1/profiles/me/files/history/?type=avatar" \
  -H "Authorization: Bearer $TOKEN"


# ----- VIEW RESUME VERSION HISTORY -----
curl -X GET "http://localhost:8000/api/v1/profiles/me/files/history/?type=resume" \
  -H "Authorization: Bearer $TOKEN"
```

### 5.3 JavaScript/Fetch Examples

```javascript
const BASE_URL = 'http://localhost:8000/api/v1';
const TOKEN = 'your_jwt_token_here';

// ----- UPLOAD AVATAR -----
async function uploadAvatar(file) {
  const formData = new FormData();
  formData.append('avatar', file);

  const response = await fetch(`${BASE_URL}/profiles/me/avatar/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${TOKEN}`
    },
    body: formData
  });

  const data = await response.json();
  console.log(data);
  return data;
}

// Usage (in browser with file input):
// const fileInput = document.getElementById('avatar-input');
// fileInput.addEventListener('change', (e) => {
//   uploadAvatar(e.target.files[0]);
// });


// ----- UPLOAD RESUME -----
async function uploadResume(file) {
  const formData = new FormData();
  formData.append('resume', file);

  const response = await fetch(`${BASE_URL}/profiles/me/resume/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${TOKEN}`
    },
    body: formData
  });

  const data = await response.json();
  console.log(data);
  return data;
}


// ----- DELETE AVATAR -----
async function deleteAvatar() {
  const response = await fetch(`${BASE_URL}/profiles/me/avatar/delete/`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${TOKEN}`
    }
  });

  const data = await response.json();
  console.log(data);
  return data;
}


// ----- DELETE RESUME -----
async function deleteResume() {
  const response = await fetch(`${BASE_URL}/profiles/me/resume/delete/`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${TOKEN}`
    }
  });

  const data = await response.json();
  console.log(data);
  return data;
}


// ----- VIEW FILE VERSION HISTORY -----
async function getFileHistory(fileType) {
  const response = await fetch(
    `${BASE_URL}/profiles/me/files/history/?type=${fileType}`,
    {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${TOKEN}`
      }
    }
  );

  const data = await response.json();
  console.log(data);
  return data;
}

// Usage:
// getFileHistory('avatar');
// getFileHistory('resume');
```

---

## 6. Error Handling Reference

### Common Error Responses

```python
# 400 Bad Request - File too large
{
  "error": "Invalid file uploaded.",
  "details": {
    "avatar": ["Avatar size (6.2MB) exceeds maximum allowed size (5MB)"]
  }
}

# 400 Bad Request - Wrong file type
{
  "error": "Invalid file uploaded.",
  "details": {
    "avatar": ["Avatar type 'image/bmp' is not allowed. Allowed types: image/jpeg, image/png, image/gif"]
  }
}

# 400 Bad Request - No file provided
{
  "error": "Invalid file uploaded.",
  "details": {
    "avatar": ["This field is required."]
  }
}

# 401 Unauthorized - No JWT token
{
  "detail": "Authentication credentials were not provided."
}

# 401 Unauthorized - Invalid token
{
  "detail": "Given token not valid for any token type"
}

# 404 Not Found - Profile not found
{
  "error": "Profile not found."
}

# 404 Not Found - No file to delete
{
  "error": "No avatar found to delete."
}

# 500 Internal Server Error - MinIO failure
{
  "error": "Failed to upload file to storage."
}
```

---

## 7. Testing Checklist

### Manual Testing Steps:

1. **Upload Avatar (Valid)**
   - ✅ Upload JPEG (< 5MB)
   - ✅ Upload PNG (< 5MB)
   - ✅ Upload GIF (< 5MB)
   - ✅ Verify URL in database
   - ✅ Verify file in MinIO (check MinIO console at http://localhost:9001)

2. **Upload Avatar (Invalid)**
   - ✅ Upload file > 5MB → expect 400 error
   - ✅ Upload BMP/TIFF → expect 400 error
   - ✅ Upload without file → expect 400 error

3. **Upload Resume (Valid)**
   - ✅ Upload PDF (< 2MB)
   - ✅ Verify URL in database
   - ✅ Verify file in MinIO

4. **Upload Resume (Invalid)**
   - ✅ Upload file > 2MB → expect 400 error
   - ✅ Upload DOCX → expect 400 error
   - ✅ Upload without file → expect 400 error

5. **File Versioning**
   - ✅ Upload avatar twice
   - ✅ Check MinIO - should have 2 files
   - ✅ Check database - should have latest URL
   - ✅ Use history endpoint - should see both versions

6. **Delete Files**
   - ✅ Delete avatar → verify URL cleared
   - ✅ Delete resume → verify URL cleared
   - ✅ Delete again → expect 404 error
   - ✅ Verify file removed from MinIO

7. **Authentication**
   - ✅ Upload without token → expect 401
   - ✅ Upload with invalid token → expect 401
   - ✅ Upload with valid token → expect 200

8. **File History**
   - ✅ Get avatar history → list all versions
   - ✅ Get resume history → list all versions
   - ✅ Download via presigned URL → file downloads correctly

### Automated Test Example (Django):

```python
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from interviews.models import UserProfile
from auth_service.models import User

class FileUploadTestCase(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

        # Create profile
        self.profile = UserProfile.objects.create(
            id=self.user.id,
            full_name='Test User'
        )

        # Get JWT token
        self.client = APIClient()
        response = self.client.post('/api/auth/login/', {
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_upload_avatar_success(self):
        # Create a fake image file
        image_content = b'fake image content'
        image_file = SimpleUploadedFile(
            "test_avatar.jpg",
            image_content,
            content_type="image/jpeg"
        )

        response = self.client.post(
            '/api/v1/profiles/me/avatar/',
            {'avatar': image_file},
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('avatar_url', response.data)

        # Verify profile updated
        self.profile.refresh_from_db()
        self.assertNotEqual(self.profile.avatar_url, '')

    def test_upload_avatar_too_large(self):
        # Create file > 5MB
        large_content = b'x' * (6 * 1024 * 1024)
        large_file = SimpleUploadedFile(
            "large.jpg",
            large_content,
            content_type="image/jpeg"
        )

        response = self.client.post(
            '/api/v1/profiles/me/avatar/',
            {'avatar': large_file},
            format='multipart'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_avatar_success(self):
        # First upload an avatar
        self.profile.avatar_url = 'http://minio:9000/user-profiles/avatars/1/test.jpg'
        self.profile.save()

        # Delete it
        response = self.client.delete('/api/v1/profiles/me/avatar/delete/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify profile updated
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.avatar_url, '')
```

---

## 8. Security Best Practices Implemented

✅ **Authentication**: All endpoints require valid JWT token
✅ **Authorization**: Users can only access their own files (`request.user.id`)
✅ **File Size Validation**: Strict limits enforced (5MB images, 2MB PDFs)
✅ **MIME Type Validation**: Whitelist of allowed content types
✅ **Filename Sanitization**: Remove special characters, prevent path traversal
✅ **Error Logging**: All errors logged with user context
✅ **Input Validation**: Serializers validate all input data
✅ **Versioning**: Old files preserved for audit trail

---

## 9. MinIO File Structure

After uploads, your MinIO buckets will look like this:

```
user-profiles/
  └── avatars/
      └── 123/  (user_id)
          ├── 2025-12-19_093000_profile.jpg     (old version)
          ├── 2025-12-19_120000_updated.png     (old version)
          └── 2025-12-19_153000_final-pic.jpg   (current - URL in DB)

user-documents/
  └── resumes/
      └── 123/  (user_id)
          ├── 2025-12-19_090000_resume_v1.pdf  (old version)
          ├── 2025-12-19_140000_resume_v2.pdf  (old version)
          └── 2025-12-19_150000_resume_v3.pdf  (current - URL in DB)
```

---

## 10. Quick Start Guide

### Step 1: Create the utilities file
Create `common/file_utils.py` with the code from section 1.

### Step 2: Update serializers
Add the serializer classes from section 2 to `interview_service/interviews/serializers.py`.

### Step 3: Add views
Add the view classes from section 3 to `interview_service/interviews/views.py`.

### Step 4: Update URLs
Add the URL patterns from section 4 to `interview_service/interviews/urls.py`.

### Step 5: Test
Use the examples from section 5 to test the implementation.

---

## 11. Customization Options

### Change File Size Limits:

In `common/file_utils.py`, modify:
```python
MAX_AVATAR_SIZE = 10 * 1024 * 1024  # Change to 10MB
MAX_RESUME_SIZE = 5 * 1024 * 1024   # Change to 5MB
```

### Add More File Types:

```python
ALLOWED_AVATAR_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
ALLOWED_RESUME_TYPES = ['application/pdf', 'application/msword',
                        'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
```

### Change Versioning Behavior:

To auto-delete old files instead of keeping versions, modify the upload views:

```python
# In AvatarUploadView.post() - add before uploading new file:
if profile.avatar_url:
    # Delete old file
    old_parsed = parse_minio_url(profile.avatar_url)
    if old_parsed:
        bucket, obj = old_parsed
        minio_client.delete_file(bucket, obj)
```

---

## Summary

This complete implementation provides:
- ✅ **Full CRUD operations** for avatar and resume files
- ✅ **JWT authentication** and authorization
- ✅ **File validation** (size, type, security)
- ✅ **Versioning support** (keeps old files)
- ✅ **Error handling** for all edge cases
- ✅ **Complete examples** in Python, cURL, and JavaScript
- ✅ **Testing guide** with examples
- ✅ **Production-ready code** with logging and security

All code is ready to copy-paste and use directly in your project!
