from django.shortcuts import render

from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from .permissions import IsOrgAdmin, IsTestUser
from rest_framework.views import APIView
from django.core.cache import cache

from .minio_utils import generate_versioned_filename, build_minio_url, parse_minio_url

from .models import *
from .serializers import *

from common.minio_client import get_minio_client

import logging

logger = logging.getLogger(__name__)


class AvatarUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_id = request.user.id

        logger.info(f"user id: {user_id}")
        try:
            profile = UserProfile.objects.get(id=user_id)
        except UserProfile.DoesNotExist:
            logger.warning(f"userProfile not found for user id: {user_id}")
            return Response({
                "error": f"userProfile not found for user : {user_id}"
            }, status=status.HTTP_404_NOT_FOUND)
        
        data = request.data
        serializer = AvatarUploadSerializer(data=data)
        if not serializer.is_valid():
            logger.warning(f"avatar validation failed for {user_id}: {serializer.errors}")
            return Response({
                "error": 'invalid file upload',
                "details": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        avatar_file = serializer.validated_data['avatar']
        object_name = generate_versioned_filename(user_id, file_type='avatar', original_filename=avatar_file.name)

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
                logger.error(f"error uploading avatar for {user_id}")
                return Response({
                    "error": "failed to upload file to storage"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            avatar_url = build_minio_url(bucket_name, object_name)

            try:
                profile.avatar_url = avatar_url
                profile.save(update_fields=['avatar_url'])
            except Exception as e:
                logger.warning(f"failed to save avatar url for {user_id}")

            return Response({
                "message": "avatar uploaded successfully.",
                "avatar_url": avatar_url,
                "profile": UserProfileSerializer(profile).data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"failed to uploading avatar for user {user_id}: {str(e)}")
            return Response({
                "error": "error occurred during upload."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def delete(self, request):
        user_id = request.user.id

        try:
            profile = UserProfile.objects.get(id=user_id)

        except UserProfile.DoesNotExist:
            logger.error(f"profile not found")
            return Response({
                "error": "profile not found"
            }, status=status.HTTP_404_NOT_FOUND)

        if not profile.avatar_url:
            logger.warning(f"avatar not found")
            return Response({
                "error": f"no avatar found to delete"
            }, status=status.HTTP_404_NOT_FOUND)
        
        parsed = parse_minio_url(profile.avatar_url)
        if not parsed:
            logger.error(f"failed to parse avatar url for user {user_id} : {profile.avatar_url}")
            return Response({
                "error": f"failed to parase avatar url"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        bucket_name, object_name = parsed

        minio_client = get_minio_client()

        try:
            if not minio_client.file_exists(bucket_name, object_name):
                logger.warning(f"avatar not found in minio for user {user_id} : {object_name}")
                profile.avatar_url = ''
                profile.save(update_fields=['avatar_url'])
                return Response({
                    "message": f"avatar reference cleared, not found in storage"
                }, status=status.HTTP_200_OK)
            
            success = minio_client.delete_file(bucket_name, object_name)

            if not success:
                logger.error(f"error deleting profile for user {user_id} : {profile.avatar_url}")
                return Response({
                    "error": f"error deleting avatar"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            profile.avatar_url = ''
            profile.save(update_fields=['avatar_url'])

            return Response({
                "message": "avatar deleted sucessfully",
                "profile": UserProfileSerializer(profile).data
            }, status=status.HTTP_200_OK)


        except Exception as e:
            logger.error(f"error occured while deleting from storage")
            return Response({
                "error": f"error occured while deleting from storage"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ResumeUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_id = request.user.id

        try:
            profile = UserProfile.objects.get(id=user_id)
        except UserProfile.DoesNotExist:
            logger.warning(f"userProfile not found")
            return Response({
                "error":"profile not found"
            }, status=status.HTTP_404_NOT_FOUND)
        
        data = request.data
        serializer = ResumeUploadSerializer(data=data)
        if not serializer.is_valid():
            logger.warning(f"resume validation failed for user {user_id} : {serializer.errors}")
            return Response({
                "error": f"resume validation failed for user {user_id} : {serializer.errors}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        resume_file = serializer.validated_data['resume']

        object_name = generate_versioned_filename(
            user_id=user_id,
            file_type='resume',
            original_filename=resume_file.name
        )

        # upload to minio
        minio_client = get_minio_client()
        bucket_name = 'user-documents'

        try:
            success = minio_client.upload_file(
                bucket_name=bucket_name,
                object_name=object_name,
                file_data = resume_file.read(),
                content_type = resume_file.content_type,
                metadata = {
                    'user_id': str(user_id),
                    'original_filename': resume_file.name,
                    'file_type': 'resume'
                }
            )

            if not success:
                logger.error(f"minio resume upload failed for user : {user_id}")
                return Response({
                    "error": "failed to upload resume"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            resume_url = build_minio_url(bucket_name, object_name)
            logger.info(f"resume url for user {user_id} : {resume_url}")

            profile.resume_url = resume_url
            profile.save(update_fields=['resume_url'])

            logger.info(f"resume uploaded sucessfully for user {user_id} : {object_name}")

            return Response({
                "message": f"resume uploaded successfully",
                "resume_url": resume_url,
                "profile": UserProfileSerializer(profile).data
            }, status=status.HTTP_200_OK)
            

        except Exception as e:
            logger.warning(f"error while uploading file for user {user_id} : {str(e)}")
            return Response({
                "error": f"error while uploading file for user {user_id}: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

    def delete(self, request):
        user_id = request.user.id

        try:
            profile = UserProfile.objects.get(id=user_id)
        except UserProfile.DoesNotExist:
            logger.warning(f"userProfile not found")
            return Response({
                "error":"profile not found"
            }, status=status.HTTP_404_NOT_FOUND)
        
        if not profile.resume_url:
            logger.warning(f"resume not found for user")
            return Response({
                "error": "no resume found to delete"
            }, status=status.HTTP_404_NOT_FOUND)
        
        parsed = parse_minio_url(profile.resume_url)
        if not parsed:
            logger.error(f"failed to parse url for user { user_id} : {profile.resume_url}")
            return Response({
                "error": f"invalid resume url format"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        bucket_name, object_name = parsed
        minio_client = get_minio_client()
        try:
            if not minio_client.file_exists(bucket_name, object_name):
                logger.warning(f"resume file not found in storage for user {user_id}: {object_name}")
                profile.resume_url = ''
                profile.save(update_fields=['resume_url'])
                return Response({
                    "message": "resume reference cleared, file not found in storage."
                }, status=status.HTTP_200_OK)

            success = minio_client.delete_file(bucket_name, object_name)

            if not success:
                logger.error(f"storage deletion failed for user {user_id}: {object_name}")
                return Response({
                    "error": "failed to delete file from storage."
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            profile.resume_url = ''
            profile.save(update_fields=['resume_url'])
            logger.info(f"resume deleted successfully for user {user_id}: {object_name}")

            return Response({
                "message": "resume deleted successfully.",
                "profile": UserProfileSerializer(profile).data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"error while deleting resume for user {user_id}: {str(e)}")
            return Response({
                "error": "error occurred during deletion."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





@api_view(['GET'])
@permission_classes([AllowAny])
def AllUserProfiles(request):
    try:
        user_profiles = UserProfile.objects.all()
        serializer = UserProfileSerializer(user_profiles, many=True)
        
        return Response({
            "data": serializer.data
        }, status=status.HTTP_200_OK)


    except UserProfile.DoesNotExist:
        logger.error(f"UserProfiles not found")


class MyProfileView(APIView):
    permission_classes = [IsTestUser]

    def get_cache_key(self, user_id):
        return f"profile:{user_id}"

    def get(self, request):
        user_id = request.user.id
        cache_key = self.get_cache_key(user_id)

        # try cache first
        # cached = cache.get(cache_key)
        # if cached:
        #     return Response(cached)

        try:
            profile = UserProfile.objects.get(pk=user_id)
        except UserProfile.DoesNotExist:
            logger.warning(f"profile not found")
            return Response({
                "error": "Profile not found."
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = UserProfileSerializer(profile)

        # cache.set(cache_key, serializer.data, timeout=300)

        return Response({
            "data": serializer.data
        }, status=status.HTTP_200_OK)
    
    def put(self, request):
        user_id = request.user.id
        # cache_key = self.get_cache_key(user_id)

        try:
            profile = UserProfile.objects.get(pk=user_id)
        except UserProfile.DoesNotExist:
            logger.error(f"Profile not found for user {user_id}")
            return Response({
                "error": "Profile not found."
            }, status=status.HTTP_404_NOT_FOUND)


        serializer = UserProfileUpdateSerializer(profile, data=request.data)

        if serializer.is_valid():
            serializer.save()


            # cache.delete(cache_key)

            logger.info(f"Profile updated (PUT) for user {user_id}")

            full_serializer = UserProfileSerializer(profile)

            return Response({
                "message": "Profile updated successfully.",
                "data": full_serializer.data
            }, status=status.HTTP_200_OK)

        logger.warning(f"Invalid data provided for PUT request by user {user_id}: {serializer.errors}")
        return Response({
            "error": "Invalid data provided.",
            "details": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        user_id = request.user.id
        cache_key = self.get_cache_key(user_id)

        try:
            profile = UserProfile.objects.get(pk=user_id)
        except UserProfile.DoesNotExist:
            logger.error(f"Profile not found for user {user_id}")
            return Response({
                "error": "Profile not found."
            }, status=status.HTTP_404_NOT_FOUND)

        # use dedicated update serializer with partial=True
        serializer = UserProfileUpdateSerializer(profile, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()

            # Invalidate cache
            cache.delete(cache_key)

            logger.info(f"Profile updated (PATCH) for user {user_id}")

            # Return full profile using read serializer
            full_serializer = UserProfileSerializer(profile)

            return Response({
                "message": "Profile updated successfully.",
                "data": full_serializer.data
            }, status=status.HTTP_200_OK)

        logger.warning(f"Invalid data provided for PATCH request by user {user_id}: {serializer.errors}")
        return Response({
            "error": "Invalid data provided.",
            "details": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


# @api_view(['GET'])
# @permission_classes([IsTestUser])
# def test_permission_endpoint(request):
#     """
#     Test endpoint to verify IsTestUser permission class.
#     This endpoint should be accessible without authentication.

#     Usage: GET /api/v1/test-permission/
#     """
#     return Response({
#         "message": "Success! IsTestUser permission is working.",
#         "description": "This endpoint uses IsTestUser permission class which allows all access.",
#         "user_authenticated": request.user.is_authenticated if request.user else False,
#         "user": str(request.user) if request.user and request.user.is_authenticated else "Anonymous",
#         "note": "This permission class should only be used for testing. Remove it in production!"
#     }, status=status.HTTP_200_OK)



