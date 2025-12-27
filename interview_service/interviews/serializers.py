
from rest_framework import serializers
from .models import *
from .minio_utils import validate_resume, validate_avatar
from django.core.exceptions import ValidationError as DjangoValidationError

import logging
logger = logging.getLogger(__name__)

class AvatarUploadSerializer(serializers.Serializer):
    avatar = serializers.ImageField(required=True)

    def validate_avatar(self, value):
        try:
            validate_avatar(value)
        except DjangoValidationError as e:
            logger.warning(f"error validating avatar: {str(e)}")
            raise serializers.ValidationError(str(e))
        return value
    
class ResumeUploadSerializer(serializers.Serializer):
    resume = serializers.FileField(required=True)

    def validate_resume(self, value):
        try:
            validate_resume(value)
        except DjangoValidationError as e:
            logger.warning(f"error validating resume: {str(e)}")
            raise serializers.ValidationError(str(e))
        return value
    



class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = "__all__"
        read_only_fields = [
            'id',
            'email',
            'username',
            'role',
            'date_of_birth',
            'age',
            'is_active',
            'auth_synced_at',
            'created_at',
            'profile_updated_at',
        ]

    def validate_skills(self, value):

        if not isinstance(value, list):
            raise serializers.ValidationError("skills must be a list.")

        for skill in value:
            if not isinstance(skill, str):
                raise serializers.ValidationError("each skill must be a string.")

        return value

    def validate_experience_years(self, value):
        if value < 0:
            raise serializers.ValidationError("experience years cannot be negative.")

        if value > 70:
            raise serializers.ValidationError("experience years seems unreasonably high.")
        return value

    def validate_phone(self, value):
        if value and not value.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '').isdigit():
            raise serializers.ValidationError("phone number must contain only digits and basic formatting characters (+, -, (), space).")

        return value

    def validate_email_notifications(self, value):
        if not isinstance(value, bool):
            raise serializers.ValidationError("email notifications must be a boolean value.")

        return value


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            'full_name',
            'phone',
            'bio',
            # 'avatar_url',
            # 'resume_url',
            'current_job_title',
            'current_company',
            'experience_years',
            'skills',
            'linkedin_url',
            'github_url',
            'portfolio_url',
            'preferred_language',
            'user_timezone',
            'email_notifications',
        ]

    def validate_skills(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("skills must be a list.")

        for skill in value:
            if not isinstance(skill, str):
                raise serializers.ValidationError("each skill must be a string.")

        return value

    def validate_experience_years(self, value):
        if value < 0:
            raise serializers.ValidationError("experience years cannot be negative.")

        if value > 70:
            raise serializers.ValidationError("experience years seems unreasonably high.")
        return value

    def validate_phone(self, value):
        if value and not value.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '').isdigit():
            raise serializers.ValidationError("phone number must contain only digits and basic formatting characters (+, -, (), space).")
        return value

    def validate_preferred_language(self, value):
        if value and len(value) > 10:
            raise serializers.ValidationError("language code is too long.")
        return value

    def validate_user_timezone(self, value):
        if value and len(value) > 50:
            raise serializers.ValidationError("timezone string is too long.")
        return value


class PublicProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'full_name', 'avatar_url', 'current_job_title', 'linkedin_url', 'github_url', 'age']

class JobRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobRole
        fields = "__all__"

    def validate(self, data):
        tech = data.get("technical_weight", self.instance.technical_weight if self.instance else 0.4)
        behav = data.get('behavioral_weight', self.instance.behavioral_weight if self.instance else 0.3)
        situa = data.get('situational_weight', self.instance.situational_weight if self.instance else 0.2)
        gen = data.get('general_weight', self.instance.general_weight if self.instance else 0.1)

        if not (0.99 <= (tech + behav + situa + gen) <= 1.01):
            raise serializers.ValidationError("weights must sum to 1.0")
        return data
    
