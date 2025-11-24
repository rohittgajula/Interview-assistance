"""
Kafka configuration for interview-assistance microservices.
Centralizes Kafka settings, topic names, and connection parameters.
"""
import os
from decouple import config


# Kafka Connection Settings
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:29092')

# Topic Names
class Topics:
    """Kafka topic names following the pattern: service.entity.events"""
    USER_EVENTS = os.getenv('KAFKA_USER_EVENTS_TOPIC', 'user.events')
    ORGANIZATION_EVENTS = os.getenv('KAFKA_ORGANIZATION_EVENTS_TOPIC', 'organization.events')
    INTERVIEW_EVENTS = os.getenv('KAFKA_INTERVIEW_EVENTS_TOPIC', 'interview.events')
    BLOOM_FILTER_EVENTS = os.getenv('KAFKA_BLOOM_FILTER_EVENTS_TOPIC', 'bloom-filter.events')


# Producer Configuration
PRODUCER_CONFIG = {
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
    'client.id': 'interview-assistance-producer',
    'acks': 'all',  # Wait for all in-sync replicas
    'retries': 3,
    'retry.backoff.ms': 1000,
    'max.in.flight.requests.per.connection': 5,
    'compression.type': 'snappy',
    'linger.ms': 10,  # Small batching delay
    'batch.size': 16384,
    'enable.idempotence': True,  # Exactly-once semantics
}


# Consumer Configuration Base
def get_consumer_config(group_id, **kwargs):
    """
    Get consumer configuration with group_id.

    Args:
        group_id: Consumer group identifier
        **kwargs: Additional config overrides

    Returns:
        dict: Consumer configuration
    """
    config = {
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': group_id,
        'auto.offset.reset': 'earliest',  # Start from beginning if no offset
        'enable.auto.commit': True,
        'auto.commit.interval.ms': 5000,
        'session.timeout.ms': 45000,
        'max.poll.interval.ms': 300000,  # 5 minutes
        'isolation.level': 'read_committed',  # Only read committed messages
    }
    config.update(kwargs)
    return config


# Consumer Group IDs
class ConsumerGroups:
    """Consumer group identifiers for different services"""
    BLOOM_FILTER_USER_EVENTS = 'bloom-filter-user-events-consumer'
    INTERVIEW_USER_EVENTS = 'interview-user-events-consumer'
    ANALYTICS_ALL_EVENTS = 'analytics-all-events-consumer'


# Event Types
class EventTypes:
    """Event type identifiers"""
    # User events
    USER_CREATED = 'user.created'
    USER_UPDATED = 'user.updated'
    USER_DELETED = 'user.deleted'
    USER_LOGIN = 'user.login'
    USER_LOGOUT = 'user.logout'

    # Organization events
    ORGANIZATION_CREATED = 'organization.created'
    ORGANIZATION_UPDATED = 'organization.updated'
    ORGANIZATION_DELETED = 'organization.deleted'
    MEMBER_ADDED = 'member.added'
    MEMBER_REMOVED = 'member.removed'

    # Interview events
    INTERVIEW_SCHEDULED = 'interview.scheduled'
    INTERVIEW_STARTED = 'interview.started'
    INTERVIEW_COMPLETED = 'interview.completed'
    INTERVIEW_CANCELLED = 'interview.cancelled'
    FEEDBACK_SUBMITTED = 'feedback.submitted'

    # Bloom filter events
    FILTER_REBUILD_STARTED = 'filter.rebuild.started'
    FILTER_REBUILD_COMPLETED = 'filter.rebuild.completed'
    FILTER_CLEARED = 'filter.cleared'
    FILTER_CAPACITY_WARNING = 'filter.capacity.warning'
