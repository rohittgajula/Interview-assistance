from django.shortcuts import render

from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny

from .models import *
from .serializers import *

import logging

logger = logging.getLogger(__name__)

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


