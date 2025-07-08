from django.contrib.gis.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta
import random
import string

class User(AbstractUser):
    """
    Custom user model for minglin with phone-based authentication.
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
    # Remove email requirement - use phone as username
    email = models.EmailField(blank=True, null=True)
    
    # Override username to use phone number
    username = models.CharField(max_length=32, unique=True, default='')
    
    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.phone
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.phone} ({self.role})"

class OTP(models.Model):
    """
    OTP model for phone verification.
    """
    phone = models.CharField(max_length=32)
    otp_code = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        indexes = [
            models.Index(fields=['phone', 'created_at']),
        ]
    
    def __str__(self):
        return f"OTP for {self.phone}"
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    @classmethod
    def generate_otp(cls, phone):
        """Generate a new OTP for the given phone number."""
        # Delete any existing OTPs for this phone
        cls.objects.filter(phone=phone).delete()
        
        # Generate 6-digit OTP
        otp_code = ''.join(random.choices(string.digits, k=6))
        
        # Create OTP with 10 minutes expiry
        otp = cls.objects.create(
            phone=phone,
            otp_code=otp_code,
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        
        return otp
    
    @classmethod
    def verify_otp(cls, phone, otp_code):
        """Verify OTP for the given phone number."""
        try:
            otp = cls.objects.get(
                phone=phone,
                otp_code=otp_code,
                is_verified=False
            )
            
            if otp.is_expired():
                return None, "OTP has expired"
            
            otp.is_verified = True
            otp.save()
            return otp, None
            
        except cls.DoesNotExist:
            return None, "Invalid OTP"

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
