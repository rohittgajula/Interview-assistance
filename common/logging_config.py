import os
import logging
import logging.config

logger = logging.getLogger(__name__)


def setup_logging(service_name):
    """
    Setup basic logging for a service.

    Args:
        service_name: Name of the service for logging identification
    """
    logger.info(f"Logging setup for {service_name}")


def get_logging_config(service_name, log_level='INFO'):
    """
    Get Django logging configuration.

    Args:
        service_name: Name of the service
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        dict: Django LOGGING configuration
    """
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
        'handlers': {
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
        },
        'loggers': {
            'django': {
                'handlers': ['console', 'file'],
                'level': 'INFO',
                'propagate': False,
            },
            'django.request': {
                'handlers': ['console', 'file'],
                'level': 'ERROR',
                'propagate': False,
            },
            'django.db.backends': {
                'handlers': ['console', 'file'],
                'level': 'WARNING',
                'propagate': False,
            },
            service_name: {
                'handlers': ['console', 'file'],
                'level': log_level,
                'propagate': False,
            },
        },
        'root': {
            'handlers': ['console', 'file'],
            'level': log_level,
        },
    }
