import requests
import logging
from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)

@shared_task(bind=True, queue='bloom_filter_queue')
def clear_bloom_filter(self):
    try:
        # Import here to avoid circular imports
        from .service import bloom_service
        
        result = bloom_service.clear_all()
        if result:
            logger.info("Successfully cleared bloom filters")
            # Rebuild after clearing
            rebuild_bloom_filter.delay()  # type: ignore[misc]
        else:
            logger.error("Failed to clear bloom filters")
        return result
    except Exception as e:
        logger.error(f"Error in clear_bloom_filter task: {e}")
        return False

@shared_task(bind=True, queue='bloom_filter_queue')
def rebuild_bloom_filter(self):

    try:
        # Import here to avoid circular imports
        from .service import bloom_service
        from common.kafka_producer import publish_event
        from common.events import FilterRebuildStartedEvent
        import uuid
        
        # Fetch users from auth service
        # auth_url = f"{settings.AUTH_SERVICE_URL}/api/users/"
        
        # try:
        #     response = requests.get(auth_url, timeout=30)
        #     if response.status_code == 200:
        #         users = response.json()
        #         
        #         # Add all usernames and emails to bloom filter
        #         username_count = 0
        #         email_count = 0
        #         
        #         for user in users:
        #             if 'username' in user and user['username']:
        #                 bloom_service.add_username(user['username'])
        #                 username_count += 1
        #             
        #             if 'email' in user and user['email']:
        #                 bloom_service.add_email(user['email'])
        #                 email_count += 1
        #         
        #         logger.info(f"Rebuilt bloom filter: {username_count} usernames, {email_count} emails")
        #         return True
        #     else:
        #         logger.error(f"Failed to fetch users from auth service: {response.status_code}")
        #         return False
        # 
        # except requests.RequestException as e:
        #     logger.error(f"Request error while fetching users: {e}")
        #     return False

        # New Kafka implementation
        rebuild_id = str(uuid.uuid4())
        event = FilterRebuildStartedEvent(
            rebuild_id=rebuild_id,
            filter_type="all"
        )
        publish_event("bloom.filter.events", event, key=rebuild_id)
        logger.info(f"Published FilterRebuildStartedEvent: {rebuild_id}")
        return True
            
    except Exception as e:
        logger.error(f"Error in rebuild_bloom_filter task: {e}")
        return False

@shared_task(bind=True, queue='bloom_filter_queue')
def add_username_to_filter(self, username):

    try:
        from .service import bloom_service
        result = bloom_service.add_username(username)
        logger.info(f"Added username {username} to bloom filter: {result}")
        return result
    except Exception as e:
        logger.error(f"Error adding username {username} to bloom filter: {e}")
        return False

@shared_task(bind=True, queue='bloom_filter_queue')
def add_email_to_filter(self, email):
    try:
        from .service import bloom_service
        result = bloom_service.add_email(email)
        logger.info(f"Added email {email} to bloom filter: {result}")
        return result
    except Exception as e:
        logger.error(f"Error adding email {email} to bloom filter: {e}")
        return False

@shared_task(bind=True, queue='bloom_filter_queue')
def process_user_update(self, user_data, action='create'):
    try:
        if action in ['create', 'update']:
            username = user_data.get('username')
            email = user_data.get('email')
            
            results = []
            if username:
                results.append(add_username_to_filter.delay(username))  # type: ignore[misc]
            if email:
                results.append(add_email_to_filter.delay(email))  # type: ignore[misc]
            
            logger.info(f"Processed user {action}: username={username}, email={email}")
            return True
        
        elif action == 'delete':
            # For delete, we don't remove from bloom filter (by design)
            # Bloom filters don't support deletion
            logger.info(f"User deleted - no action needed for bloom filter")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error processing user update: {e}")
        return False
    

    