
import uuid
from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from datetime import date


class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None, role="candidate", **extra_fields):
        if not email:
            raise ValueError("email is required")
        if not username:
            raise ValueError("username is required")
        
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(email, username, password, role="organization_admin", **extra_fields)
    

class Organization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    domain = models.CharField(max_length=255, blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True, null=True)
    logo_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    website = models.URLField(max_length=500, blank=True, null=True)


    def __str__(self):
        return self.name


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ("organization_admin", "Organization Admin"),
        ("interviewer", "Interviewer"),
        ("candidate", "Candidate"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    date_of_birth = models.DateField()
    age = models.PositiveIntegerField(editable=False)

    # organization = models.ForeignKey(
    #     Organization, null=True, blank=True, on_delete=models.CASCADE, related_name="users"
    # )


    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    # objects = UserManager()
    objects: UserManager = UserManager()


    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def save(self, *args, **kwargs):
        if self.date_of_birth:
            today = date.today()
            self.age = today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        super().save(*args, **kwargs)

    @property
    def is_interviewer(self):
        return self.role == "interviewer"

    @property
    def is_candidate(self):
        return self.role == "candidate"

    @property
    def is_org_admin(self):
        return self.role == "organization_admin"

    def __str__(self):
        return f"{self.username} ({self.role})"
    
    # @property
    # def organization_name(self):
    #     return self.organization.username if self.organization else None


class Membership(models.Model):
    ROLE_IN_ORG = [
        ("admin", "Admin"),
        ("member", "Member"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="memberships")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="memberships")
    role_in_org = models.CharField(max_length=10, choices=ROLE_IN_ORG, default="member")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "organization")

    def __str__(self):
        return f"{self.user.username} -> {self.organization.name} ({self.role_in_org})"

