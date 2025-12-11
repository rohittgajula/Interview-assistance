#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bloom_filter_service.settings')

    # Add the parent directory to sys.path to allow importing common modules
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    from common.logging_config import setup_logging
    setup_logging("bloom_filter_service")

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
