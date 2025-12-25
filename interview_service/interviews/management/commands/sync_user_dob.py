from django.core.management.base import BaseCommand
import psycopg2
import os
from interviews.models import UserProfile


class Command(BaseCommand):
    help = 'Sync date_of_birth for existing users from auth_service to interview_service'

    def handle(self, *args, **options):
        self.stdout.write("Starting date_of_birth sync for existing users...")

        # Connect to auth database
        auth_conn = psycopg2.connect(
            dbname=os.getenv('AUTH_DB_NAME', 'InterviewAssistance_AuthService'),
            user=os.getenv('AUTH_USER', 'rohit'),
            password=os.getenv('AUTH_PASSWORD', 'rohit2710'),
            host=os.getenv('AUTH_HOST', 'auth_db'),
            port=os.getenv('AUTH_PORT', '5432')
        )

        try:
            auth_cursor = auth_conn.cursor()

            # Get all users with date_of_birth from auth service
            auth_cursor.execute("""
                SELECT id, username, date_of_birth, age
                FROM users_user
                WHERE date_of_birth IS NOT NULL
            """)

            auth_users = auth_cursor.fetchall()
            self.stdout.write(f"Found {len(auth_users)} users in auth database with date_of_birth")

            updated_count = 0
            skipped_count = 0

            for user_id, username, date_of_birth, age in auth_users:
                try:
                    # Find the corresponding user profile in interview service
                    profile = UserProfile.objects.get(id=user_id)

                    # Only update if date_of_birth is currently None
                    if profile.date_of_birth is None:
                        profile.date_of_birth = date_of_birth
                        profile.age = age
                        profile.save()
                        updated_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"✓ Updated {username} (ID: {user_id}) - DOB: {date_of_birth}, Age: {age}"
                            )
                        )
                    else:
                        skipped_count += 1
                        self.stdout.write(f"- Skipped {username} (already has DOB: {profile.date_of_birth})")

                except UserProfile.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(
                            f"⚠ User {username} (ID: {user_id}) not found in interview service"
                        )
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"✗ Error updating {username}: {e}")
                    )

            self.stdout.write("\n=== Summary ===")
            self.stdout.write(self.style.SUCCESS(f"Updated: {updated_count}"))
            self.stdout.write(f"Skipped: {skipped_count}")
            self.stdout.write(f"Total processed: {len(auth_users)}")

        finally:
            auth_cursor.close()
            auth_conn.close()

        self.stdout.write(self.style.SUCCESS("Sync complete!"))
