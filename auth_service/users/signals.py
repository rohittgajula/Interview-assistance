# auth_service/users/signals.py
# Django signals for User model to sync with bloom filter service

import logging
# import requests
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import User
# from django.conf import settings
from common.kafka_producer import publish_event
from common.events import UserCreatedEvent, UserUpdatedEvent, UserDeletedEvent

logger = logging.getLogger('users.signals')



# this function sends webhook to bloom filter service when user changes
# def send_webhook_to_bloom_filter(user_data, action):
#
#     try:
#         # Update this URL to use nginx route
#         webhook_url = "http://nginx/bloom/api/webhook/"
#         
#         payload = {
#             'user': user_data,
#             'action': action
#         }
#         
#         response = requests.post(webhook_url, json=payload, timeout=5)
#         if response.status_code == 200:
#             logger.info(f"Successfully sent {action} webhook for user {user_data.get('username')}")
#         else:
#             logger.error(f"Failed to send webhook: {response.status_code} - {response.text}")
#             
#     except requests.RequestException as e:
#         logger.error(f"Error sending webhook to bloom filter service: {e}")
#     except Exception as e:
#         logger.error(f"Unexpected error sending webhook: {e}")



# this signal handles user creation and updates
@receiver(post_save, sender=User)
def user_saved_handler(sender, instance, created, **kwargs):

    try:
        user_id = str(instance.id)
        username = getattr(instance, 'username', '')
        email = getattr(instance, 'email', '')
        role = getattr(instance, 'role', 'user') # Assuming role exists or default
        date_of_birth = getattr(instance, 'date_of_birth', None)
        age = getattr(instance, 'age', None)
        is_active = getattr(instance, 'is_active', True)

        if created:
            event = UserCreatedEvent(
                user_id=user_id,
                username=username,
                email=email,
                role=role,
                date_of_birth=date_of_birth.isoformat() if date_of_birth else None,
                age=age,
                is_active=is_active
            )
            publish_event("user.events", event, key=user_id)
            logger.info(f"Published UserCreatedEvent for: {username}")
        else:
            event = UserUpdatedEvent(
                user_id=user_id,
                username=username,
                email=email,
                role=role,
                date_of_birth=date_of_birth.isoformat() if date_of_birth else None
            )
            publish_event("user.events", event, key=user_id)
            logger.info(f"Published UserUpdatedEvent for: {username}")

    except Exception as e:
        logger.error(f"Error in user_saved_handler: {e}")



@receiver(post_delete, sender=User)
def user_deleted_handler(sender, instance, **kwargs):
    try:
        user_id = str(instance.id)
        username = getattr(instance, 'username', '')
        email = getattr(instance, 'email', '')

        event = UserDeletedEvent(
            user_id=user_id,
            username=username,
            email = email
        )
        publish_event("user.events", event, key=user_id)
        logger.info(f"published UserDeletedEvent for: {username}")

    except Exception as e:
        logger.error(f"error in user_deleted_handler: {e}")






