"""
Kafka producer wrapper for publishing events.
Provides a singleton producer with automatic JSON serialization and error handling.
"""
import logging
import atexit
from typing import Optional, Dict, Any
from confluent_kafka import Producer
from confluent_kafka import KafkaError, KafkaException

from .kafka_config import PRODUCER_CONFIG
from .events import BaseEvent, serialize_event

logger = logging.getLogger(__name__)


class KafkaProducerSingleton:
    """
    Singleton wrapper for Kafka Producer.
    Ensures only one producer instance exists per process.
    """
    _instance: Optional[Producer] = None
    _initialized: bool = False

    @classmethod
    def get_instance(cls, config: Optional[Dict[str, Any]] = None) -> Producer:
        """
        Get or create the Kafka producer instance.

        Args:
            config: Optional producer configuration override

        Returns:
            Producer: Confluent Kafka Producer instance
        """
        if cls._instance is None:
            producer_config = config or PRODUCER_CONFIG
            cls._instance = Producer(producer_config)
            cls._initialized = True
            logger.info("Kafka producer initialized")

            # Register cleanup on exit
            atexit.register(cls.close)

        return cls._instance

    @classmethod
    def close(cls):
        """Close the producer and flush pending messages"""
        if cls._instance is not None and cls._initialized:
            logger.info("Flushing and closing Kafka producer")
            cls._instance.flush(timeout=30)
            cls._instance = None
            cls._initialized = False


class EventProducer:
    """
    High-level event producer for publishing domain events.
    Handles serialization, error handling, and delivery callbacks.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize EventProducer.

        Args:
            config: Optional producer configuration override
        """
        self.producer = KafkaProducerSingleton.get_instance(config)

    def _delivery_callback(self, err, msg):
        """
        Callback invoked when a message is delivered or failed.

        Args:
            err: KafkaError if delivery failed
            msg: Message object
        """
        if err:
            logger.error(
                f"Message delivery failed: {err}. "
                f"Topic: {msg.topic()}, Partition: {msg.partition()}"
            )
        else:
            logger.debug(
                f"Message delivered to {msg.topic()} "
                f"[partition {msg.partition()}] at offset {msg.offset()}"
            )

    def publish_event(
        self,
        topic: str,
        event: BaseEvent,
        key: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> bool:

        try:
            # Serialize event
            value = serialize_event(event)

            # Convert key to bytes if provided
            key_bytes = key.encode('utf-8') if key else None

            # Convert headers to list of tuples if provided
            headers_list = None
            if headers:
                headers_list = [(k, v.encode('utf-8')) for k, v in headers.items()]

            # Produce message
            self.producer.produce(
                topic=topic,
                value=value,
                key=key_bytes,
                headers=headers_list,
                callback=self._delivery_callback
            )

            # Trigger delivery reports
            self.producer.poll(0)

            logger.info(
                f"Event queued: {event.event_type} to topic {topic} "
                f"(key: {key or 'None'})"
            )
            return True

        except BufferError:
            logger.error(
                f"Local producer queue is full ({len(self.producer)} messages). "
                "Consider increasing queue.buffering.max.messages or poll() more often."
            )
            return False

        except KafkaException as e:
            logger.error(f"Kafka error while publishing event: {e}")
            return False

        except Exception as e:
            logger.error(f"Unexpected error while publishing event: {e}")
            return False

    def flush(self, timeout: int = 30):
        """
        Flush all buffered messages.

        Args:
            timeout: Maximum time to wait in seconds
        """
        remaining = self.producer.flush(timeout)
        if remaining > 0:
            logger.warning(f"{remaining} messages were not delivered within timeout")
        else:
            logger.info("All messages delivered successfully")

    def close(self):
        """Close the producer"""
        KafkaProducerSingleton.close()


# Convenience function for quick event publishing
def publish_event(
    topic: str,
    event: BaseEvent,
    key: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None
) -> bool:
    """
    Convenience function to publish an event without managing producer instance.

    Args:
        topic: Kafka topic name
        event: Event instance to publish
        key: Optional message key
        headers: Optional message headers

    Returns:
        bool: True if successfully queued
    """
    producer = EventProducer()
    return producer.publish_event(topic, event, key, headers)
