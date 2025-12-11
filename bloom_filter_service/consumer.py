
import os
import django
import logging
import sys

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bloom_filter_service.settings')
django.setup()

from common.kafka_consumer import EventConsumer
from common.events import UserCreatedEvent, UserUpdatedEvent, UserDeletedEvent
from bloom_filter.service import bloom_service

logger = logging.getLogger(__name__)

class BloomFilterEventConsumer(EventConsumer):
    def process_event(self, event, raw_message):
        try:
            if isinstance(event, (UserCreatedEvent, UserUpdatedEvent)):
                username = getattr(event, 'username', None)
                email = getattr(event, 'email', None)
                
                if username:
                    bloom_service.add_username(username)
                    # logger.info(f"Added username to bloom filter: {username}")
                
                if email:
                    bloom_service.add_email(email)
                    # logger.info(f"Added email to bloom filter: {email}")
                
                return True
            
            elif isinstance(event, UserDeletedEvent):
                # Bloom filters don't support deletion, so we ignore this
                logger.info(f"Ignored UserDeletedEvent for: {event.username}")
                return True
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing event: {e}")
            return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    logger.info("Starting Bloom Filter Service Kafka Consumer...")
    
    topics = ['user.events']
    group_id = 'bloom-filter-service-consumer-group'
    
    consumer = BloomFilterEventConsumer(topics, group_id)
    consumer.consume()
