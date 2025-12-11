
import os
import django
import logging
import sys

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_service.settings')
django.setup()

from common.kafka_consumer import EventConsumer
from common.events import UserCreatedEvent, UserUpdatedEvent, UserDeletedEvent
from interviews.models import UserProfile
from datetime import datetime

logger = logging.getLogger(__name__)

class InterviewEventConsumer(EventConsumer):
    def process_event(self, event, raw_message):
        try:
            if isinstance(event, UserCreatedEvent):
                logger.info(f"User created: {event.username} (ID: {event.user_id})")
                self._handle_user_created(event)
                return True

            elif isinstance(event, UserUpdatedEvent):
                logger.info(f"User updated: {event.user_id}")
                self._handle_user_updated(event)
                return True

            elif isinstance(event, UserDeletedEvent):
                logger.info(f"User deleted: {event.username} (ID: {event.user_id})")
                self._handle_user_deleted(event)
                return True

            return True

        except Exception as e:
            logger.error(f"Error processing event: {e}")
            return False
        
    def _handle_user_updated(self, event: UserUpdatedEvent):
        try:
            if event.user_id:
                try:
                    profile = UserProfile.objects.update(id=event.user_id)

                    if event.username is not None:
                        profile.username = event.username
                    if event.email is not None:
                        profile.email = event.email
                    if event.role is not None:
                        profile.role = event.role
                    profile.save()
                    logger.info(f"update userProfile for user {event.username} - {event.user_id}")
                except UserProfile.DoesNotExist:
                    logger.error(f"userProfile not found for user {event.username} - {event.user_id}")

        except Exception as e:
            logger.error(f"error updating userProfile for {event.user_id}: {e}")
        
    def _handle_user_deleted(self, event: UserDeletedEvent):
        try:
            if event.user_id:
                try:
                    profile = UserProfile.objects.get(id=event.user_id)
                    profile.delete()
                    logger.info(f"userProfile deleted for user {event.username} - {event.user_id}")
                except UserProfile.DoesNotExist:
                    logger.error(f"userProfile not found for user {event.username} - {event.user_id}")

                # if profile:
                #     profile.delete()
                #     logger.info(f"userProfile deleted for user {event.username} - {event.user_id}")

        except Exception as e:
            logger.error(f"error deleting userProfile for {event.username} - {event.user_id}: {e}")

    def _handle_user_created(self, event: UserCreatedEvent):
        try:
            # Parse date_of_birth if provided
            date_of_birth = None
            if event.date_of_birth:
                try:
                    date_of_birth = datetime.fromisoformat(event.date_of_birth).date()
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid date_of_birth format: {event.date_of_birth}, error: {e}")

            profile, created = UserProfile.objects.update_or_create(
                id=event.user_id,
                defaults={
                    'email': event.email,
                    'username': event.username,
                    'role': event.role,
                    'date_of_birth': date_of_birth,
                    'age': event.age,
                    'is_active': event.is_active,
                }
            )

            if created:
                logger.info(f"Created UserProfile for {event.username} (ID: {event.user_id})")
            else:
                logger.info(f"Updated UserProfile for {event.username} (ID: {event.user_id})")

        except Exception as e:
            logger.error(f"Error creating/updating UserProfile for {event.user_id}: {e}")
            raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    logger.info("Starting Interview Service Kafka Consumer...")

    topics = ['user.events']
    group_id = 'interview-service-consumer-group'

    consumer = InterviewEventConsumer(topics, group_id)
    consumer.consume()
