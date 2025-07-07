from django.contrib.gis.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """
    Custom user model for minglin.
    Extends Django's AbstractUser and adds extra fields.
    """
    ROLE_CHOICES = (
        ('user', 'User'),
        ('business', 'Business'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=32, unique=True)
    preferences = models.JSONField(default=list, blank=True)
    location = models.PointField(geography=True, null=True, blank=True)
    notifications_push = models.BooleanField(default=True)
    # name, email, password, etc. are inherited from AbstractUser

    def __str__(self):
        return f"{self.username} ({self.role})"

class Business(models.Model):
    """
    Business profile linked to a User (owner).
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    contact_phone = models.CharField(max_length=32, blank=True)
    owner_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='businesses')

    def __str__(self):
        return self.name

class Deal(models.Model):
    """
    Deal model for business offers, with geospatial location.
    """
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='deals')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='deals/', null=True, blank=True)
    category = models.CharField(max_length=128, blank=True)
    cta = models.CharField(max_length=255, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    location = models.PointField(geography=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    views = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['end_time']),
        ]

    def __str__(self):
        return self.title

# See README.md and inline comments for documentation.
