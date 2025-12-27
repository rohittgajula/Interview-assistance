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
            # Silence Daphne/ASGI server DEBUG logs
            'daphne': {
                'handlers': handlers_list,
                'level': 'INFO',
                'propagate': False,
            },
            'django.server': {
                'handlers': handlers_list,
                'level': 'INFO',
                'propagate': False,
            },
            # Silence asyncio DEBUG logs
            'asyncio': {
                'handlers': handlers_list,
                'level': 'WARNING',
                'propagate': False,
            },
            service_name: {
                'handlers': handlers_list,
                'level': log_level,
                'propagate': False,
            },
            # Application loggers (interviews, auth, etc.)
            'interviews': {
                'handlers': handlers_list,
                'level': log_level,
                'propagate': False,
            },
            'auth': {
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
