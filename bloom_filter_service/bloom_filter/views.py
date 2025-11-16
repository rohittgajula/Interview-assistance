from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .service import bloom_service
from .tasks import add_username_to_filter, add_email_to_filter, rebuild_bloom_filter, clear_bloom_filter
import logging

logger = logging.getLogger(__name__)

class CheckUsernameView(APIView):
    
    def post(self, request):
        username = request.data.get('username')
        if not username:
            return Response(
                {'error': 'Username is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        exists = bloom_service.check_username(username)
        return Response({
            'username': username,
            'might_exist': exists,
            'message': 'Username might exist' if exists else 'Username probably does not exist'
        })

class CheckEmailView(APIView):    
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response(
                {'error': 'Email is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        exists = bloom_service.check_email(email)
        return Response({
            'email': email,
            'might_exist': exists,
            'message': 'Email might exist' if exists else 'Email probably does not exist'
        })

class CheckBothView(APIView):
    
    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        
        if not username and not email:
            return Response(
                {'error': 'Username or email is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        result = {}
        
        if username:
            username_exists = bloom_service.check_username(username)
            result['username'] = {
                'value': username,
                'might_exist': username_exists,
                'message': 'Username might exist' if username_exists else 'Username probably does not exist'
            }
        
        if email:
            email_exists = bloom_service.check_email(email)
            result['email'] = {
                'value': email,
                'might_exist': email_exists,
                'message': 'Email might exist' if email_exists else 'Email probably does not exist'
            }
        
        return Response(result)

class AddUsernameView(APIView):

    def post(self, request):
        username = request.data.get('username')
        if not username:
            return Response(
                {'error': 'Username is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add asynchronously
        task = add_username_to_filter.delay(username)
        
        return Response({
            'username': username,
            'task_id': task.id,
            'message': 'Username added to bloom filter'
        })

class AddEmailView(APIView):
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response(
                {'error': 'Email is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add asynchronously
        task = add_email_to_filter.delay(email)
        
        return Response({
            'email': email,
            'task_id': task.id,
            'message': 'Email added to bloom filter'
        })

class AddUserView(APIView):
    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        
        if not username and not email:
            return Response(
                {'error': 'Username or email is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tasks = []
        
        if username:
            task = add_username_to_filter.delay(username)
            tasks.append({'type': 'username', 'value': username, 'task_id': task.id})
        
        if email:
            task = add_email_to_filter.delay(email)
            tasks.append({'type': 'email', 'value': email, 'task_id': task.id})
        
        return Response({
            'tasks': tasks,
            'message': 'User data added to bloom filter'
        })

class StatsView(APIView):
    def get(self, request):
        stats = bloom_service.get_stats()
        return Response(stats)

class RebuildView(APIView):    
    def post(self, request):
        task = rebuild_bloom_filter.delay()
        return Response({
            'task_id': task.id,
            'message': 'Bloom filter rebuild started'
        })

class ClearView(APIView):
    def post(self, request):
        task = clear_bloom_filter.delay()
        return Response({
            'task_id': task.id,
            'message': 'Bloom filter clear started'
        })

class HealthCheckView(APIView):
    def get(self, request):
        try:
            # Test Redis connection
            bloom_service.redis_client.ping()
            
            return Response({
                'status': 'healthy',
                'message': 'Bloom filter service is running'
            })
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return Response({
                'status': 'unhealthy',
                'message': str(e)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

class WebhookView(APIView):
    def post(self, request):
        try:
            user_data = request.data.get('user', {})
            action = request.data.get('action', 'create')  # create, update, delete
            
            if not user_data:
                return Response(
                    {'error': 'User data is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Process asynchronously
            from .tasks import process_user_update
            task = process_user_update.delay(user_data, action)
            
            return Response({
                'task_id': task.id,
                'message': f'User {action} processed',
                'user_data': user_data
            })
            
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return Response(
                {'error': 'Internal server error'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        


        