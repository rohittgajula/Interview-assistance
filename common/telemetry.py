"""
OpenTelemetry instrumentation for all services
Provides automatic tracing, metrics, and logging to SigNoz
"""

import os
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION, DEPLOYMENT_ENVIRONMENT
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

# Instrumentations
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor


def configure_opentelemetry(service_name: str, service_version: str = "1.0.0"):
    """
    Configure OpenTelemetry for a Django service

    Args:
        service_name: Name of the service (e.g., 'auth_service', 'interview_service')
        service_version: Version of the service
    """

    # Get configuration from environment variables
    otlp_endpoint = os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://otel-collector:4317')
    environment = os.getenv('DEPLOYMENT_ENVIRONMENT', 'development')

    # Create resource with service information
    resource = Resource.create({
        SERVICE_NAME: service_name,
        SERVICE_VERSION: service_version,
        DEPLOYMENT_ENVIRONMENT: environment,
        "service.namespace": "interview-assistance",
    })

    # Configure Tracing
    trace_provider = TracerProvider(resource=resource)
    otlp_span_exporter = OTLPSpanExporter(
        endpoint=otlp_endpoint,
        insecure=True  # Use insecure for local development
    )
    trace_provider.add_span_processor(BatchSpanProcessor(otlp_span_exporter))
    trace.set_tracer_provider(trace_provider)

    # Configure Metrics
    otlp_metric_exporter = OTLPMetricExporter(
        endpoint=otlp_endpoint,
        insecure=True
    )
    metric_reader = PeriodicExportingMetricReader(
        otlp_metric_exporter,
        export_interval_millis=30000  # Export every 30 seconds
    )
    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[metric_reader]
    )
    metrics.set_meter_provider(meter_provider)

    # Auto-instrument common libraries
    DjangoInstrumentor().instrument()

    try:
        Psycopg2Instrumentor().instrument()
    except Exception as e:
        print(f"Warning: Could not instrument psycopg2: {e}")

    try:
        RedisInstrumentor().instrument()
    except Exception as e:
        print(f"Warning: Could not instrument Redis: {e}")

    RequestsInstrumentor().instrument()

    print(f"OpenTelemetry configured for {service_name}")
    print(f"Sending telemetry to: {otlp_endpoint}")


def get_tracer(name: str):
    """Get a tracer instance for manual instrumentation"""
    return trace.get_tracer(name)


def get_meter(name: str):
    """Get a meter instance for custom metrics"""
    return metrics.get_meter(name)
