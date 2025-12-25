

from django.conf import settings
import os
import re
from datetime import datetime
from django.core.exceptions import ValidationError
import mimetypes

import logging
logger = logging.getLogger(__name__)

MAX_AVATAR_SIZE = 5*1024*1024       # this is 5mb
MAX_RESUME_SIZE = 5*1024*1024
MAX_DOCUMENT_SIZE = 10*1024*1024


ALLOWED_AVATAR_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
ALLOWED_RESUME_TYPES = ['application/pdf']
ALLOWED_DOCUMENT_TYPES = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']



def validate_file_size(file, max_size_bytes, file_type="File"):
    if file.size > max_size_bytes:
        max_size_mb = max_size_bytes / (1024*1024)
        logger.warning(f"file size is above expected size: {file.size / (1024*1024)}")
        raise ValidationError(
            f"{file_type} size ({file.size / (1024*1024):.2f}MB) exceeds"
            f"maximum allowed size {max_size_mb:.0f}MB"
        )


def validate_file_type(file, allowed_types, file_type="File"):
    guessed_type = mimetypes.guess_type(file.name)
    logger.info(f"guessed file type: {guessed_type}")
    if file.content_type not in allowed_types:
        logger.warning(f"file type not allowed")
        raise ValidationError(
            f"file type not allowed {file.content_type}"
            f"allowed types: {allowed_types}"
        )
    
    # to guess the file type

    if guessed_type and guessed_type[0] and guessed_type[0] not in allowed_types:
        raise ValidationError(
            f"{file_type} extension does not match an allowed type. "
            f"allowed types: {', '.join(allowed_types)}"
        )


def sanitize_filename(filename):
    filename = os.path.basename(filename)

    # remove and replace special chars
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    filename = filename.strip('. ')

    name, ext = os.path.splitext(filename)
    if len(name) > 100:
        name = name[:100]

    return f"{name}{ext}"

def generate_versioned_filename(user_id, file_type, original_filename):
    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
    sanitized_file_name = sanitize_filename(original_filename)

    type_dirs = {
        "avatar": 'avatars',
        'resume': 'resumes',
        'document': 'documents'
    }

    dir_name = type_dirs.get(file_type, 'files')
    return f"{dir_name}/{user_id}/{timestamp}_{sanitized_file_name}"


# returns bucketname and object anme
def parse_minio_url(file_url):
    if not file_url:
        return None
    
    try:
        if '://' in file_url:
            file_url = file_url.split('://', 1)[1]
            if '/' in file_url:
                file_url = file_url.split('/', 1)[1]
        
        file_url = file_url.lstrip('/')
        # splits into 2 bucket name and object name
        parts = file_url.split('/', 1)
        if len(parts) == 2:
            logger.info(f"parased url bucket_name:{parts[0]}, url:{parts[1]}")
            return parts[0], parts[1]
        return None
    except Exception:
        logger.warning(f"error in parsing")
        return None


def build_minio_url(bucket_name: str, object_name: str) -> str:
    # Use public endpoint for URLs that will be accessed from browsers
    endpoint = getattr(settings, 'MINIO_PUBLIC_ENDPOINT', 'localhost:9000')
    secure = getattr(settings, 'MINIO_SECURE', False)
    protocol = 'https' if secure else 'http'

    return f"{protocol}://{endpoint}/{bucket_name}/{object_name}"

def validate_avatar(file):
    validate_file_size(file, MAX_AVATAR_SIZE, "Avatar")
    validate_file_type(file, ALLOWED_AVATAR_TYPES, "Avatar")

def validate_resume(file):
    validate_file_size(file, MAX_RESUME_SIZE, "Resume")
    validate_file_type(file, ALLOWED_RESUME_TYPES, "Resume")

def validate_document(file):
    validate_file_size(file, MAX_DOCUMENT_SIZE, "Document")
    validate_file_type(file, ALLOWED_DOCUMENT_TYPES, "Document")


