
from rest_framework.views import APIView

from django.contrib.auth import authenticate, get_user_model
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes

from typing import Any, Dict, cast

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from django.core.paginator import Paginator

from .models import Organization, Membership
from .serializers import RegisterSerializer, UserSerializer, LoginSerializer, OrganizationSerializer, MembershipSerializer

User = get_user_model()
import logging

logger = logging.getLogger(__name__)

class UsersListView(APIView):
    """
    API endpoint to list all users for bloom filter rebuild
    This should be called only by internal services
    """
    permission_classes = []  # Allow unauthenticated access for internal service calls

    def get(self, request):
        try:
            # Get pagination parameters
            page = request.GET.get('page', 1)
            page_size = request.GET.get('page_size', 1000)  # Large page size for bulk operations
            
            # Get all users
            users = User.objects.all().values('id', 'username', 'email')
            
            # Paginate if needed
            paginator = Paginator(users, page_size)
            page_obj = paginator.get_page(page)
            
            # Format response
            user_list = []
            for user in page_obj:
                user_list.append({
                    'id': user['id'],
                    'username': user['username'] or '',
                    'email': user['email'] or '',
                })
            
            response_data = {
                'users': user_list,
                'pagination': {
                    'current_page': page_obj.number,
                    'total_pages': paginator.num_pages,
                    'total_count': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous(),
                }
            }
            
            # If no pagination needed (small dataset), return all users directly
            if paginator.num_pages == 1:
                response_data = user_list
            
            logger.info(f"Returned {len(user_list)} users for bloom filter rebuild")
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"Error in UsersListView: {e}")
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# /api/auth/register/
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):

    try:
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                "error": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        

        """
        here ide was showing error for get so this approach
        """
        # data: Dict[str, Any] = serializer.validated_data
        data = cast(Dict[str, Any], serializer.validated_data)
        # data = serializer.validated_data

        email = data.get("email")
        username = cast(str, data.get("username"))
        password = data.get("password")
        role = data.get("role")
        date_of_birth = data.get("date_of_birth")
        # org_id = data.get("organization")

        if User.objects.filter(email=email).exists():
            return Response({"error": "Email already registered"}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already taken"}, status=status.HTTP_400_BAD_REQUEST)
        
        # organization = None
        # if org_id:
        #     try:
        #         organization = Organization.objects.get(id=org_id)
        #     except Organization.DoesNotExist:
        #         return Response({"error": "Invalid organization ID"}, status=status.HTTP_400_BAD_REQUEST)
            
        user = User.objects.create_user(
            email=email,
            username=username,
            password=password,
            role=role,
            date_of_birth=date_of_birth,
            # organization=organization,
        )

        return Response(
            {"message": "User registered successfully", "user": UserSerializer(user).data},
            status=status.HTTP_201_CREATED,
        )
    except Exception as e:
        logger.warning(f"error registering user: {e}")
        return Response({
            "error": f"error registering user: {e}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




# /api/auth/login/
@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):

    serializer = LoginSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            "error": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    


    data = cast(Dict[str, Any], serializer.validated_data)
    
    email = data.get("email")
    password = cast(str, data.get("password"))

    # user = authenticate(request, username=email, password=password)
    user = authenticate(request, email=email, password=password)
    
    if user is None:
        return Response({
            "error": "invalid creadentials"
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    if not user.is_active:
        return Response({
            "error": "user account is disabled"
        }, status=status.HTTP_403_FORBIDDEN)
    
    refresh = RefreshToken.for_user(user)
    return Response({
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": UserSerializer(user).data,
    }, status=status.HTTP_200_OK)



# /api/auth/token/refresh/
# We’ll just wrap the built-in SimpleJWT refresh view
class CustomTokenRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]


# /api/auth/logout/
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_user(request):
    refresh_token = request.data.get("refresh")

    if not refresh_token:
        return Response({"error": "Refresh token required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({"message": "Successfully logged out"}, status=status.HTTP_205_RESET_CONTENT)
    except Exception:
        return Response({"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST)



# /api/auth/me/
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_current_user(request):
    user = request.user
    serializer = UserSerializer(user)
    return Response(serializer.data, status=status.HTTP_200_OK)



def is_org_admin(user, organization_id=None):
    # Superusers bypass
    if user.is_superuser:
        return True

    if not organization_id:
        return False

    return Membership.objects.filter(
        user=user, organization_id=organization_id, role_in_org="admin"
    ).exists()



@api_view(['GET'])
def list_organizations(request):
    # list all oragnizations
    orgs = Organization.objects.all().order_by("name")
    serializer = OrganizationSerializer(orgs, many=True)
    return Response({
        "data": serializer.data
    }, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_organization(request, org_id):
    try:
        org = Organization.objects.get(id=org_id)
    except Organization.DoesNotExist:
        return Response({"error": "Organization not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = OrganizationSerializer(org)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_organization(request):
    if request.user.role != "organization_admin":
        return Response({
            "error": "only organization admins can create organizations"
        }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = OrganizationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            "error": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    org = serializer.save()

    Membership.objects.create(user=request.user, organization=org, role_in_org="admin")

    return Response({
        "message": "organization created successfully",
        "organization": serializer.data
    }, status=status.HTTP_201_CREATED)



@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_organization(request, org_id):

    try:
        org = Organization.objects.get(id=org_id)
    except Organization.DoesNotExist:
        return Response({
            "error": "oragnization doesnot exist"
        }, status=status.HTTP_404_NOT_FOUND)
    
    if not is_org_admin(request.user, org.id):
        return Response({
            "error": "you are not authorized to update this organization"
        }, status=status.HTTP_403_FORBIDDEN)

    
    serializer = OrganizationSerializer(org, data=request.data, partial=(request.method == 'PATCH'))
    if not serializer.is_valid():
        return Response({
            "error": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    serializer.save()
    return Response({
        "message": "oragnization updated sucessfully",
        "data": serializer.data
    }, status=status.HTTP_200_OK)



@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_organization(request, org_id):

    try:
        org = Organization.objects.get(id=org_id)
    except Organization.DoesNotExist:
        return Response({
            "error": "organization doesnot exist"
        }, status=status.HTTP_404_NOT_FOUND)
    
    if not is_org_admin(request.user, org.id):
        return Response({
            "error": "you are not authorized to delete this organization"
        }, status=status.HTTP_403_FORBIDDEN)
    
    org.delete()
    return Response({
        "message": "organization deleted successfully"
    }, status=status.HTTP_204_NO_CONTENT)



@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_members(request, org_id):
    if not is_org_admin(request.user, org_id):
        return Response({"error": "Only admins can view members"},
                        status=status.HTTP_403_FORBIDDEN)

    members = Membership.objects.filter(organization_id=org_id)
    serializer = MembershipSerializer(members, many=True)
    return Response({
        "data": serializer.data
    }, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_member(request, org_id):
    if not is_org_admin(request.user, org_id):
        return Response({"error": "Only admins can add members"},
                        status=status.HTTP_403_FORBIDDEN)

    user_id = request.data.get("user_id")
    role_in_org = request.data.get("role_in_org", "member")

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    membership, created = Membership.objects.get_or_create(
        user=user, organization_id=org_id, defaults={"role_in_org": role_in_org}
    )

    if not created:
        return Response({"error": "User is already a member"}, status=status.HTTP_400_BAD_REQUEST)

    return Response({"message": "Member added successfully"}, status=status.HTTP_201_CREATED)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def remove_member(request, org_id, user_id):
    if not is_org_admin(request.user, org_id):
        return Response({"error": "Only admins can remove members"},
                        status=status.HTTP_403_FORBIDDEN)

    try:
        membership = Membership.objects.get(user_id=user_id, organization_id=org_id)
    except Membership.DoesNotExist:
        return Response({"error": "Membership not found"}, status=status.HTTP_404_NOT_FOUND)

    membership.delete()
    return Response({"message": "Member removed successfully"}, status=status.HTTP_204_NO_CONTENT)







