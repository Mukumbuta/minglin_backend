from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'businesses', views.BusinessViewSet, basename='business')
router.register(r'deals', views.DealViewSet, basename='deal')
router.register(r'saved-deals', views.SavedDealViewSet, basename='saved-deal')
router.register(r'notifications', views.NotificationViewSet, basename='notification')
router.register(r'customer-requests', views.CustomerRequestViewSet, basename='customer-request')

urlpatterns = [
    # Healthcheck endpoint for SRE/monitoring
    path('healthcheck/', views.healthcheck, name='healthcheck'),
    # Phone-based Auth endpoints
    path('auth/send-otp/', views.SendOTPView.as_view(), name='send-otp'),
    path('auth/verify-otp/', views.VerifyOTPView.as_view(), name='verify-otp'),
    # Deals customer/public endpoints
    path('deals/customer/', views.CustomerDealsView.as_view(), name='customer-deals'),
    path('deals/customer/<int:pk>/', views.CustomerDealDetailView.as_view(), name='customer-deal-detail'),
    path('deals/my/', views.MyDealsView.as_view(), name='my-deals'),
    # User profile endpoints (me, preferences, location)
    path('users/me/', views.MeView.as_view(), name='me'),
    path('users/preferences/', views.UserPreferencesView.as_view(), name='user-preferences'),
    path('users/location/', views.UserLocationView.as_view(), name='user-location'),
    # Analytics endpoints
    path('analytics/', views.AnalyticsView.as_view(), name='analytics'),
    # Search endpoints
    path('deals/search/', views.DealSearchView.as_view(), name='deal-search'),
    # Business logo upload
    path('businesses/logo/', views.BusinessLogoUploadView.as_view(), name='business-logo-upload'),
    # Deal interaction tracking
    path('deals/<int:deal_id>/interaction/', views.record_deal_interaction, name='record-deal-interaction'),
    # Customer request endpoints
    path('business/requests/', views.BusinessRequestNotificationsView.as_view(), name='business-requests'),
    # Main RESTful endpoints
    path('', include(router.urls)),
]

# See README.md and inline comments for documentation. 