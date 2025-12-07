
import os
import django
import logging
import sys

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_service.settings')
django.setup()

from common.kafka_consumer import EventConsumer
from common.kafka_producer import publish_event
from common.events import FilterRebuildStartedEvent, UserCreatedEvent
from users.models import User

logger = logging.getLogger(__name__)

class AuthEventConsumer(EventConsumer):
    def process_event(self, event, raw_message):
        try:
            if isinstance(event, FilterRebuildStartedEvent):
                logger.info(f"Received FilterRebuildStartedEvent: {event.rebuild_id}")
                self.replay_users()
                return True
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing event: {e}")
            return False

    def replay_users(self):
        logger.info("Starting user replay for bloom filter rebuild...")
        users = User.objects.all()
        count = 0
        
        for user in users:
            try:
                user_id = str(user.id)
                username = getattr(user, 'username', '')
                email = getattr(user, 'email', '')
                role = getattr(user, 'role', 'user')

                event = UserCreatedEvent(
                    user_id=user_id,
                    username=username,
                    email=email,
                    role=role
                )
                publish_event("user.events", event, key=user_id)
                count += 1
            except Exception as e:
                logger.error(f"Error replaying user {user.id}: {e}")
        
        logger.info(f"Completed user replay. Published {count} events.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    from common.tracing import setup_tracing
    setup_tracing("auth_service_consumer")

    logger.info("Starting Auth Service Kafka Consumer...")
    
    topics = ['bloom.filter.events']
    group_id = 'auth-service-consumer-group'
    
    consumer = AuthEventConsumer(topics, group_id)
    consumer.consume()
