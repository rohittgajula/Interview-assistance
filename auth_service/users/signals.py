# auth_service/users/signals.py
# Django signals for User model to sync with bloom filter service

import logging
import requests
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import User
from django.conf import settings

logger = logging.getLogger('users.signals')



# this function sends webhook to bloom filter service when user changes
def send_webhook_to_bloom_filter(user_data, action):

    try:
        # Update this URL to use nginx route
        webhook_url = "http://nginx/bloom/api/webhook/"
        
        payload = {
            'user': user_data,
            'action': action
        }
        
        response = requests.post(webhook_url, json=payload, timeout=5)
        if response.status_code == 200:
            logger.info(f"Successfully sent {action} webhook for user {user_data.get('username')}")
        else:
            logger.error(f"Failed to send webhook: {response.status_code} - {response.text}")
            
    except requests.RequestException as e:
        logger.error(f"Error sending webhook to bloom filter service: {e}")
    except Exception as e:
        logger.error(f"Unexpected error sending webhook: {e}")



# this signal handles user creation and updates
@receiver(post_save, sender=User)
def user_saved_handler(sender, instance, created, **kwargs):

    try:
        user_data = {
            'id': str(instance.id),  # Convert UUID to string for JSON serialization
            'username': getattr(instance, 'username', ''),
            'email': getattr(instance, 'email', ''),
        }

        action = 'create' if created else 'update'

        # Send to bloom filter service asynchronously
        # You can use Celery here if you have it set up
        send_webhook_to_bloom_filter(user_data, action)

        logger.info(f"User {action} signal processed for: {user_data['username']}")

    except Exception as e:
        logger.error(f"Error in user_saved_handler: {e}")





# this signal handles user deletion
@receiver(post_delete, sender=User)
def user_deleted_handler(sender, instance, **kwargs):
    try:
        user_data = {
            'id': str(instance.id),  # Convert UUID to string for JSON serialization
            'username': getattr(instance, 'username', ''),
            'email': getattr(instance, 'email', ''),
        }

        send_webhook_to_bloom_filter(user_data, 'delete')

        logger.info(f"User delete signal processed for: {user_data['username']}")

    except Exception as e:
        logger.error(f"Error in user_deleted_handler: {e}")


