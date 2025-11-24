"""
Kafka consumer wrapper for consuming events.
Provides base classes for building event-driven consumers.
"""
import logging
import signal
import sys
from typing import List, Callable, Optional, Dict, Any
from confluent_kafka import Consumer, KafkaError, KafkaException

from .kafka_config import get_consumer_config
from .events import BaseEvent, deserialize_event_auto

logger = logging.getLogger(__name__)


class EventConsumer:
    """
    Base class for Kafka event consumers.
    Handles subscription, message polling, and graceful shutdown.
    """

    def __init__(
        self,
        topics: List[str],
        group_id: str,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize EventConsumer.

        Args:
            topics: List of topics to subscribe to
            group_id: Consumer group ID
            config: Optional consumer configuration overrides
        """
        self.topics = topics
        self.group_id = group_id
        self.running = False

        # Get consumer config
        consumer_config = get_consumer_config(group_id)
        if config:
            consumer_config.update(config)

        # Create consumer
        self.consumer = Consumer(consumer_config)

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info(f"Consumer initialized for topics: {topics}, group: {group_id}")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()

    def subscribe(self):
        """Subscribe to topics"""
        self.consumer.subscribe(self.topics)
        logger.info(f"Subscribed to topics: {self.topics}")

    def process_event(self, event: BaseEvent, raw_message) -> bool:
        """
        Process a single event. Override this method in subclasses.

        Args:
            event: Deserialized event object
            raw_message: Raw Kafka message for accessing metadata

        Returns:
            bool: True if processing succeeded, False otherwise
        """
        raise NotImplementedError("Subclasses must implement process_event()")

    def on_error(self, error: Exception, raw_message):
        """
        Handle errors during event processing. Override to customize.

        Args:
            error: Exception that occurred
            raw_message: Raw Kafka message
        """
        logger.error(f"Error processing message: {error}", exc_info=True)

    def consume(self, poll_timeout: float = 1.0):
        """
        Start consuming messages from subscribed topics.

        Args:
            poll_timeout: Timeout for poll() in seconds
        """
        self.running = True
        self.subscribe()

        logger.info("Starting message consumption...")

        try:
            while self.running:
                # Poll for messages
                msg = self.consumer.poll(timeout=poll_timeout)

                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        # End of partition event
                        logger.debug(
                            f"Reached end of partition {msg.partition()} "
                            f"at offset {msg.offset()}"
                        )
                    else:
                        # Error
                        logger.error(f"Consumer error: {msg.error()}")
                    continue

                try:
                    # Deserialize event
                    event = deserialize_event_auto(msg.value())

                    logger.debug(
                        f"Received event: {event.event_type} from "
                        f"{msg.topic()}[{msg.partition()}] at offset {msg.offset()}"
                    )

                    # Process event
                    success = self.process_event(event, msg)

                    if not success:
                        logger.warning(
                            f"Event processing returned False: {event.event_type}"
                        )

                except Exception as e:
                    self.on_error(e, msg)

        except KeyboardInterrupt:
            logger.info("Interrupted by user")

        finally:
            self.shutdown()

    def shutdown(self):
        """Gracefully shutdown the consumer"""
        if self.running:
            logger.info("Shutting down consumer...")
            self.running = False
            self.consumer.close()
            logger.info("Consumer closed")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.shutdown()


class FunctionBasedConsumer(EventConsumer):
    """
    Consumer that processes events using a provided callback function.
    Useful for simple event handling without subclassing.
    """

    def __init__(
        self,
        topics: List[str],
        group_id: str,
        handler: Callable[[BaseEvent, Any], bool],
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize FunctionBasedConsumer.

        Args:
            topics: List of topics to subscribe to
            group_id: Consumer group ID
            handler: Function to handle events (event, raw_message) -> bool
            config: Optional consumer configuration overrides
        """
        super().__init__(topics, group_id, config)
        self.handler = handler

    def process_event(self, event: BaseEvent, raw_message) -> bool:
        """
        Process event using the provided handler function.

        Args:
            event: Deserialized event object
            raw_message: Raw Kafka message

        Returns:
            bool: Result from handler function
        """
        return self.handler(event, raw_message)


# Convenience function for simple consumption
def consume_events(
    topics: List[str],
    group_id: str,
    handler: Callable[[BaseEvent, Any], bool],
    config: Optional[Dict[str, Any]] = None,
    poll_timeout: float = 1.0
):
    """
    Convenience function to start consuming events with a handler function.

    Args:
        topics: List of topics to subscribe to
        group_id: Consumer group ID
        handler: Function to handle events
        config: Optional consumer configuration
        poll_timeout: Poll timeout in seconds

    Example:
        def my_handler(event, msg):
            print(f"Received: {event.event_type}")
            return True

        consume_events(['user.events'], 'my-consumer', my_handler)
    """
    consumer = FunctionBasedConsumer(topics, group_id, handler, config)
    consumer.consume(poll_timeout)
