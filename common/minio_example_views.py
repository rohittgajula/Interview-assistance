"""
Example Django View for handling interview audio uploads with MinIO
Add this to your interview_service views for reference
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from common.minio_client import get_minio_client
import json
import uuid
from datetime import timedelta


@csrf_exempt
@require_http_methods(["POST"])
def upload_interview_audio(request):
    """
    Upload interview audio file to MinIO
    
    Expected: multipart/form-data with 'audio_file' and 'interview_id'
    """
    try:
        # Get uploaded file
        audio_file = request.FILES.get('audio_file')
        interview_id = request.POST.get('interview_id')
        
        if not audio_file or not interview_id:
            return JsonResponse({
                'error': 'Missing audio_file or interview_id'
            }, status=400)
        
        # Get MinIO client
        minio_client = get_minio_client()
        
        # Generate unique filename
        file_extension = audio_file.name.split('.')[-1]
        object_name = f'interviews/{interview_id}/audio_{uuid.uuid4()}.{file_extension}'
        
        # Upload to MinIO
        success = minio_client.upload_file(
            bucket_name='interview-audio',
            object_name=object_name,
            file_data=audio_file.read(),
            content_type=audio_file.content_type or 'audio/mpeg',
            metadata={
                'interview_id': str(interview_id),
                'original_filename': audio_file.name,
                'uploaded_by': str(request.user.id) if request.user.is_authenticated else 'anonymous'
            }
        )
        
        if success:
            # Generate presigned URL for download (valid for 24 hours)
            download_url = minio_client.get_presigned_url(
                bucket_name='interview-audio',
                object_name=object_name,
                expires=timedelta(hours=24)
            )
            
            return JsonResponse({
                'success': True,
                'object_name': object_name,
                'download_url': download_url,
                'message': 'Audio file uploaded successfully'
            })
        else:
            return JsonResponse({
                'error': 'Failed to upload file'
            }, status=500)
            
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def get_interview_audio_url(request, interview_id, audio_filename):
    """
    Get presigned URL for an interview audio file
    
    Args:
        interview_id: ID of the interview
        audio_filename: Name of the audio file
    """
    try:
        minio_client = get_minio_client()
        object_name = f'interviews/{interview_id}/{audio_filename}'
        
        # Check if file exists
        if not minio_client.file_exists('interview-audio', object_name):
            return JsonResponse({
                'error': 'Audio file not found'
            }, status=404)
        
        # Generate presigned URL (valid for 1 hour)
        download_url = minio_client.get_presigned_url(
            bucket_name='interview-audio',
            object_name=object_name,
            expires=timedelta(hours=1)
        )
        
        return JsonResponse({
            'download_url': download_url
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_interview_audio(request, interview_id, audio_filename):
    """
    Delete an interview audio file
    
    Args:
        interview_id: ID of the interview
        audio_filename: Name of the audio file
    """
    try:
        minio_client = get_minio_client()
        object_name = f'interviews/{interview_id}/{audio_filename}'
        
        success = minio_client.delete_file('interview-audio', object_name)
        
        if success:
            return JsonResponse({
                'success': True,
                'message': 'Audio file deleted successfully'
            })
        else:
            return JsonResponse({
                'error': 'Failed to delete file'
            }, status=500)
            
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def list_interview_recordings(request, interview_id):
    """
    List all recordings for a specific interview
    
    Args:
        interview_id: ID of the interview
    """
    try:
        minio_client = get_minio_client()
        
        # List all files in the interview directory
        files = minio_client.list_files(
            bucket_name='interview-audio',
            prefix=f'interviews/{interview_id}/'
        )
        
        # Generate presigned URLs for each file
        recordings = []
        for file_name in files:
            url = minio_client.get_presigned_url(
                bucket_name='interview-audio',
                object_name=file_name,
                expires=timedelta(hours=1)
            )
            recordings.append({
                'filename': file_name.split('/')[-1],
                'path': file_name,
                'download_url': url
            })
        
        return JsonResponse({
            'interview_id': interview_id,
            'recordings': recordings,
            'count': len(recordings)
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)
