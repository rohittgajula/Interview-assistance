#!/usr/bin/env python
"""
Script to sync date_of_birth for existing users from auth_service to interview_service.
This is a one-time fix for users created before the date_of_birth sync was implemented.
"""

import os
import sys
import django
import psycopg2
from datetime import datetime

# Setup Django for interview_service
sys.path.insert(0, '/app/interview_service')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview_service.settings')
django.setup()

from interviews.models import UserProfile

def sync_dob_from_auth():
    """Sync date_of_birth from auth DB to interview DB for existing users"""

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
        print(f"Found {len(auth_users)} users in auth database with date_of_birth")

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
                    print(f"✓ Updated {username} (ID: {user_id}) - DOB: {date_of_birth}, Age: {age}")
                else:
                    skipped_count += 1
                    print(f"- Skipped {username} (already has DOB: {profile.date_of_birth})")

            except UserProfile.DoesNotExist:
                print(f"⚠ User {username} (ID: {user_id}) not found in interview service")
            except Exception as e:
                print(f"✗ Error updating {username}: {e}")

        print(f"\n=== Summary ===")
        print(f"Updated: {updated_count}")
        print(f"Skipped: {skipped_count}")
        print(f"Total processed: {len(auth_users)}")

    finally:
        auth_cursor.close()
        auth_conn.close()

if __name__ == "__main__":
    print("Starting date_of_birth sync for existing users...")
    sync_dob_from_auth()
    print("Sync complete!")
