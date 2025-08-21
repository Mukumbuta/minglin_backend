from django.contrib import admin
from .models import Deal, Business, User, SavedDeal, Notification, DealAnalytics, OTP, CustomerRequest

@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ['title', 'business', 'category', 'is_active', 'created_at']
    list_filter = ['is_active', 'category', 'created_at']
    search_fields = ['title', 'description', 'business__name']
    readonly_fields = ['views', 'clicks', 'created_at', 'updated_at']
    
    # Disable the map widget for the location field
    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'location':
            kwargs['widget'] = admin.widgets.AdminTextareaWidget
        return super().formfield_for_dbfield(db_field, **kwargs)

@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner_user', 'contact_phone']
    search_fields = ['name', 'owner_user__phone']

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['phone', 'role', 'first_name', 'last_name']
    list_filter = ['role']
    search_fields = ['phone', 'first_name', 'last_name']

@admin.register(SavedDeal)
class SavedDealAdmin(admin.ModelAdmin):
    list_display = ['user', 'deal', 'saved_at']
    list_filter = ['saved_at']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']

@admin.register(DealAnalytics)
class DealAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['deal', 'user', 'action_type', 'created_at']
    list_filter = ['action_type', 'created_at']

@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ['phone', 'otp_code', 'created_at', 'expires_at', 'is_used']
    list_filter = ['is_used', 'created_at']

@admin.register(CustomerRequest)
class CustomerRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'category', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
