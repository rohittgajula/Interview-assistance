import os
import logging
import logging.config

# Import OpenTelemetry logging components
try:
    from opentelemetry._logs import set_logger_provider
    from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
    from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
    from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME
    OTEL_LOGGING_AVAILABLE = True
except ImportError:
    OTEL_LOGGING_AVAILABLE = False

logger = logging.getLogger(__name__)


def setup_logging(service_name):
    """
    Setup basic logging for a service.

    Args:
        service_name: Name of the service for logging identification
    """
    logger.info(f"Logging setup for {service_name}")


def get_otel_logging_handler(service_name):
    """
    Create OpenTelemetry logging handler for sending logs to SigNoz.

    Args:
        service_name: Name of the service

    Returns:
        LoggingHandler or None if OTEL is not available
    """
    # Check if telemetry is enabled
    telemetry_enabled = os.getenv('ENABLE_TELEMETRY', 'false').lower() == 'true'
    if not telemetry_enabled:
        return None

    if not OTEL_LOGGING_AVAILABLE:
        return None

    try:
        otlp_endpoint = os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://host.docker.internal:4317')

        # Create resource with service name
        resource = Resource.create({SERVICE_NAME: service_name})

        # Create OTLP log exporter
        otlp_exporter = OTLPLogExporter(
            endpoint=otlp_endpoint,
            insecure=True
        )

        # Create logger provider
        logger_provider = LoggerProvider(resource=resource)
        set_logger_provider(logger_provider)

        # Add batch processor
        logger_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_exporter))

        # Create logging handler
        handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)

        return handler
    except Exception as e:
        print(f"Warning: Failed to create OTLP logging handler: {e}")
        return None


def get_logging_config(service_name, log_level='INFO'):
    """
    Get Django logging configuration with OpenTelemetry support.

    Args:
        service_name: Name of the service
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        dict: Django LOGGING configuration
    """
    handlers_list = ['console', 'file']
    handlers_dict = {
        'console': {
            'level': log_level,
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'file': {
            'level': log_level,
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': f'logs/{service_name}.log',
            'maxBytes': 1024 * 1024 * 15,  # 15MB
            'backupCount': 10,
            'formatter': 'json',
        },
    }

    # Add OTLP handler if available
    otel_handler = get_otel_logging_handler(service_name)
    if otel_handler:
        # Store the handler instance globally so it can be used
        import sys
        sys._otel_logging_handler = otel_handler
        handlers_dict['otlp'] = {
            'level': 'INFO',  # Only send INFO and above to SigNoz
            '()': lambda: sys._otel_logging_handler,
        }
        handlers_list.append('otlp')
        print(f"OTLP logging handler configured for {service_name}")

    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'verbose': {
                'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
                'style': '{',
            },
            'simple': {
                'format': '{levelname} {message}',
                'style': '{',
            },
            'json': {
                'format': '{"time": "%(asctime)s", "level": "%(levelname)s", "service": "' + service_name + '", "message": "%(message)s", "module": "%(module)s", "function": "%(funcName)s", "line": %(lineno)d}',
            },
        },
        'filters': {
            'require_debug_true': {
                '()': 'django.utils.log.RequireDebugTrue',
            },
        },
        'handlers': handlers_dict,
        'loggers': {
            'django': {
                'handlers': handlers_list,
                'level': 'INFO',
                'propagate': False,
            },
            'django.request': {
                'handlers': handlers_list,
                'level': 'ERROR',
                'propagate': False,
            },
            'django.db.backends': {
                'handlers': handlers_list,
                'level': 'WARNING',
                'propagate': False,
            },
            service_name: {
                'handlers': handlers_list,
                'level': log_level,
                'propagate': False,
            },
        },
        'root': {
            'handlers': handlers_list,
            'level': log_level,
        },
    }
