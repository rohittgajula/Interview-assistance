"""
Management command to sync users from auth_service to interview_service.
This is useful when the consumer missed events or for initial data population.
"""
from django.core.management.base import BaseCommand
from interviews.models import UserProfile
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Sync users from auth_service to create/update UserProfiles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--auth-service-url',
            type=str,
            default='http://auth_service:8000',
            help='Base URL for auth_service (default: http://auth_service:8000)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be synced without actually syncing'
        )

    def handle(self, *args, **options):
        auth_service_url = options['auth_service_url']
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        # Fetch users from auth_service
        try:
            # Note: You'll need to create this endpoint in auth_service or use Django shell
            # For now, this is a template - you need to implement the API endpoint
            self.stdout.write(
                self.style.ERROR(
                    'This command requires an API endpoint in auth_service to list all users.\n'
                    'Alternative: Use Option 3 below to directly query the database.'
                )
            )

            # Example if you have an API endpoint:
            # response = requests.get(f'{auth_service_url}/api/users/', timeout=30)
            # response.raise_for_status()
            # users = response.json()

            # for user in users:
            #     if dry_run:
            #         self.stdout.write(f"Would sync user: {user['username']} (ID: {user['id']})")
            #     else:
            #         UserProfile.objects.update_or_create(
            #             id=user['id'],
            #             defaults={
            #                 'username': user['username'],
            #                 'email': user['email'],
            #                 'role': user.get('role', 'user'),
            #                 'is_active': user.get('is_active', True),
            #             }
            #         )
            #         self.stdout.write(
            #             self.style.SUCCESS(f"Synced user: {user['username']}")
            #         )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error syncing users: {e}')
            )
            raise
