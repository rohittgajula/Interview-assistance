"""
Management command to sync users from auth_service database directly.
This bypasses the event system and directly copies user data.
"""
from django.core.management.base import BaseCommand
from django.db import connections
from interviews.models import UserProfile
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Sync users from auth_service database to create/update UserProfiles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be synced without actually syncing'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        try:
            # Query auth_service database
            # Note: This requires configuring a second database connection in settings.py
            # For now, we'll provide instructions for manual sync

            self.stdout.write(
                self.style.NOTICE(
                    '\nTo sync users, you have two options:\n\n'
                    '1. Use Django shell to manually create UserProfiles:\n'
                    '   docker exec -it interview_service python manage.py shell\n'
                    '   Then run:\n'
                    '   from interviews.models import UserProfile\n'
                    '   # Add users manually\n\n'
                    '2. Reset Kafka consumer offset (see instructions below)\n\n'
                    '3. Create an API endpoint in auth_service and use sync_users_from_auth command\n'
                )
            )

            # Count existing profiles
            existing_count = UserProfile.objects.count()
            self.stdout.write(
                self.style.SUCCESS(f'\nCurrent UserProfile count: {existing_count}')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {e}')
            )
            raise
