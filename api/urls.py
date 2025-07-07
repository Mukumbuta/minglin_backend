from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'businesses', views.BusinessViewSet, basename='business')
router.register(r'deals', views.DealViewSet, basename='deal')

urlpatterns = [
    # Healthcheck endpoint for SRE/monitoring
    path('healthcheck/', views.healthcheck, name='healthcheck'),
    # Auth endpoints
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    # Deals customer/public endpoints
    path('deals/customer/', views.CustomerDealsView.as_view(), name='customer-deals'),
    path('deals/my/', views.MyDealsView.as_view(), name='my-deals'),
    # User profile endpoints (me, preferences, location)
    path('users/me/', views.MeView.as_view(), name='me'),
    path('users/preferences/', views.UserPreferencesView.as_view(), name='user-preferences'),
    path('users/location/', views.UserLocationView.as_view(), name='user-location'),
    # Main RESTful endpoints
    path('', include(router.urls)),
]

# See README.md and inline comments for documentation. 