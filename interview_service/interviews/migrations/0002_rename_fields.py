# Generated manually to handle field renames

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('interviews', '0001_initial'),
    ]

    operations = [
        # Rename UserProfile fields to match updated model
        migrations.RenameField(
            model_name='userprofile',
            old_name='current_role',
            new_name='current_job_title',
        ),
        migrations.RenameField(
            model_name='userprofile',
            old_name='synced_at',
            new_name='auth_synced_at',
        ),

        # Add new fields that don't exist in initial migration
        migrations.AddField(
            model_name='userprofile',
            name='role',
            field=models.CharField(default='candidate', max_length=20),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='userprofile',
            name='date_of_birth',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='age',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='current_company',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='linkedin_url',
            field=models.URLField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='github_url',
            field=models.URLField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='portfolio_url',
            field=models.URLField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='preferred_language',
            field=models.CharField(default='en', max_length=10),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='user_timezone',
            field=models.CharField(default='UTC', max_length=50),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='email_notifications',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='profile_updated_at',
            field=models.DateTimeField(auto_now=True),
        ),

        # Update existing fields
        migrations.AlterField(
            model_name='userprofile',
            name='username',
            field=models.CharField(max_length=150, unique=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='avatar_url',
            field=models.URLField(blank=True, max_length=500),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='resume_url',
            field=models.URLField(blank=True, max_length=500),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='auth_synced_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
