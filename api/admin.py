from django.contrib import admin
from .models import User, Business, Deal, SavedDeal, Notification, DealAnalytics

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'role', 'phone', 'date_joined']
    list_filter = ['role', 'date_joined']
    search_fields = ['username', 'email', 'phone']

@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner_user', 'contact_phone', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']

@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ['title', 'business', 'category', 'is_active', 'views', 'clicks', 'created_at']
    list_filter = ['is_active', 'category', 'created_at']
    search_fields = ['title', 'description', 'business__name']

@admin.register(SavedDeal)
class SavedDealAdmin(admin.ModelAdmin):
    list_display = ['user', 'deal', 'saved_at']
    list_filter = ['saved_at']
    search_fields = ['user__username', 'deal__title']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__username', 'title', 'message']

@admin.register(DealAnalytics)
class DealAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['deal', 'user', 'action_type', 'ip_address', 'created_at']
    list_filter = ['action_type', 'created_at']
    search_fields = ['deal__title', 'user__username', 'ip_address']
