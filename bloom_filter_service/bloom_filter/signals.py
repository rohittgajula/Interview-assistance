import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings

logger = logging.getLogger(__name__)

# These signals are placeholder examples
# You would connect these to your actual User models from auth_service

# Example of how to connect signals from external services
# This would typically be done through API webhooks or message queues

def send_webhook_to_bloom_filter(user_data, action):

    import requests
    
    try:
        webhook_url = f"{settings.BLOOM_FILTER_SERVICE_URL}/api/webhook/"
        payload = {
            'user': user_data,
            'action': action
        }
        
        response = requests.post(webhook_url, json=payload, timeout=5)
        if response.status_code == 200:
            logger.info(f"Successfully sent {action} webhook for user")
        else:
            logger.error(f"Failed to send webhook: {response.status_code}")
            
    except requests.RequestException as e:
        logger.error(f"Error sending webhook: {e}")

# Example signal handlers (these would be in your auth_service)
"""
@receiver(post_save, sender=User)
def user_saved_handler(sender, instance, created, **kwargs):
    user_data = {
        'id': instance.id,
        'username': instance.username,
        'email': instance.email,
    }
    
    action = 'create' if created else 'update'
    send_webhook_to_bloom_filter(user_data, action)

@receiver(post_delete, sender=User)
def user_deleted_handler(sender, instance, **kwargs):
    user_data = {
        'id': instance.id,
        'username': instance.username,
        'email': instance.email,
    }
    
    send_webhook_to_bloom_filter(user_data, 'delete')
"""


