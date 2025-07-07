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
    logo = models.ImageField(upload_to='business_logos/', null=True, blank=True)
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
            models.Index(fields=['title']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return self.title

class SavedDeal(models.Model):
    """
    Model for users to save deals they're interested in.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_deals')
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name='saved_by')
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'deal']
        indexes = [
            models.Index(fields=['user', 'saved_at']),
        ]

    def __str__(self):
        return f"{self.user.username} saved {self.deal.title}"

class Notification(models.Model):
    """
    Notification model for user notifications.
    """
    NOTIFICATION_TYPES = (
        ('deal_expiring', 'Deal Expiring'),
        ('new_deal', 'New Deal'),
        ('deal_clicked', 'Deal Clicked'),
        ('system', 'System'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    is_read = models.BooleanField(default=False)
    related_deal = models.ForeignKey(Deal, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.title} - {self.user.username}"

class DealAnalytics(models.Model):
    """
    Analytics model for tracking deal interactions.
    """
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name='analytics')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    action_type = models.CharField(max_length=20, choices=[
        ('view', 'View'),
        ('click', 'Click'),
        ('save', 'Save'),
        ('unsave', 'Unsave'),
    ])
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['deal', 'action_type']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.deal.title} - {self.action_type}"

# See README.md and inline comments for documentation.
