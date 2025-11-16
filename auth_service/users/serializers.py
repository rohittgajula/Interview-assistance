

from rest_framework import serializers
from .models import User, Organization, Membership
from django.contrib.auth import authenticate



class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    # organization = serializers.ForeignKey()

    class Meta:
        model = User
        fields = ["email", "username", "password", "role", "date_of_birth"]

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        email = validated_data.get("email")
        username = validated_data.get("username")

        if not email or not username:
            raise serializers.ValidationError("Email and username are required.")

        user = User.objects.create_user(
            email=email,
            username=username,
            password=password,
            **validated_data
        )
        return user



class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")
        user = authenticate(email=email, password=password)
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled")
        data["user"] = user
        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "role",
            "date_of_birth",
            "age",
            "created_at",
        ]




class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ["id", "name", "domain", "industry", "logo_url", "website", "created_at"]


class MembershipSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    organization = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Membership
        fields = ["id", "user", "organization", "role_in_org", "created_at"]

