import os
import logging
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

logger = logging.getLogger(__name__)

def setup_tracing(service_name):
    # Send to otel-collector which will forward to Jaeger and generate metrics for Prometheus
    endpoint = os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://otel-collector:4318/v1/traces')
    
    resource = Resource.create(attributes={
        "service.name": service_name,
    })

    trace.set_tracer_provider(TracerProvider(resource=resource))
    
    # HTTP exporter doesn't need insecure=True for http:// endpoints
    otlp_exporter = OTLPSpanExporter(endpoint=endpoint)
    span_processor = BatchSpanProcessor(otlp_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)

    logger.info(f"Tracing setup for {service_name} with endpoint {endpoint}")

    # Instrument common libraries
    
    try:
        from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
        Psycopg2Instrumentor().instrument()
        logger.info("Instrumented psycopg2")
    except ImportError:
        logger.debug("opentelemetry-instrumentation-psycopg2 not found, skipping.")

    try:
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
        RequestsInstrumentor().instrument()
        logger.info("Instrumented requests")
    except ImportError:
        logger.debug("opentelemetry-instrumentation-requests not found, skipping.")

    try:
        from opentelemetry.instrumentation.redis import RedisInstrumentor
        RedisInstrumentor().instrument()
        logger.info("Instrumented redis")
    except ImportError:
        logger.debug("opentelemetry-instrumentation-redis not found, skipping.")

    try:
        from opentelemetry.instrumentation.confluent_kafka import ConfluentKafkaInstrumentor
        ConfluentKafkaInstrumentor().instrument()
        logger.info("Instrumented confluent_kafka")
    except ImportError:
        logger.debug("opentelemetry-instrumentation-confluent-kafka not found, skipping.")

    try:
        from opentelemetry.instrumentation.django import DjangoInstrumentor
        DjangoInstrumentor().instrument()
        logger.info("Instrumented django")
    except ImportError:
        logger.debug("opentelemetry-instrumentation-django not found, skipping.")

    try:
        from opentelemetry.instrumentation.celery import CeleryInstrumentor
        CeleryInstrumentor().instrument()
        logger.info("Instrumented celery")
    except ImportError:
        logger.debug("opentelemetry-instrumentation-celery not found, skipping.")

    return trace.get_tracer(__name__)
