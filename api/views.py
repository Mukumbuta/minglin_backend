from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.contrib.auth import authenticate
from .models import User, Business, Deal, SavedDeal, Notification, DealAnalytics, OTP, CustomerRequest
from .serializers import (
    RegisterSerializer, UserSerializer, BusinessSerializer, DealSerializer,
    SavedDealSerializer, NotificationSerializer, DealAnalyticsSerializer,
    PhoneAuthSerializer, OTPVerificationSerializer, CustomerRequestSerializer
)
from rest_framework import viewsets, generics, status, permissions, serializers
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.db.models import Q, Count, F, Sum
from django.utils import timezone
import logging
from django.http import JsonResponse
from datetime import datetime, timedelta
from .utils import notify
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView as SimpleJWTTokenRefreshView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from django.contrib.auth import get_user_model

logger = logging.getLogger('api')

# Create your views here.

@api_view(['GET'])
@permission_classes([AllowAny])
def healthcheck(request):
    """
    Healthcheck endpoint for SRE/monitoring.
    Returns HTTP 200 and status 'ok' if the API is up.
    """
    return Response({'status': 'Minglin backend is running'})

# Phone-based Auth endpoints
class SendOTPView(generics.GenericAPIView):
    """
    Send OTP to phone number for authentication.
    """
    serializer_class = PhoneAuthSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        phone = serializer.validated_data['phone']
        role = serializer.validated_data.get('role', 'user')
        
        logger.info(f"OTP request for phone: {phone}, role: {role}")
        
        try:
            # Generate OTP
            otp = OTP.generate_otp(phone)
            
            # Clean phone number for SMS (remove + if present, the notify function will add 26 prefix)
            clean_phone = phone
            if phone.startswith('+'):
                clean_phone = phone[1:]  # Remove + if present
            
            # Send SMS (notify function will add 26 prefix automatically)
            sms_result = notify(clean_phone, f'Your Minglin OTP is {otp.otp_code}. Valid for 10 minutes.')
            logger.info(f"OTP generated for {phone}: {otp.otp_code}, SMS result: {sms_result}")
            
            return Response({
                'message': 'OTP sent successfully',
                'phone': phone,
                'role': role,
                'otp_code': otp.otp_code  # Remove this in production
            })
            
        except Exception as e:
            logger.error(f"OTP generation failed: {str(e)}")
            return Response(
                {'error': 'Failed to send OTP. Please try again.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class VerifyOTPView(generics.GenericAPIView):
    """
    Verify OTP and authenticate user.
    """
    serializer_class = OTPVerificationSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        phone = serializer.validated_data['phone']
        otp_code = serializer.validated_data['otp_code']
        role = serializer.validated_data.get('role', 'user')
        first_name = serializer.validated_data.get('first_name', '')
        last_name = serializer.validated_data.get('last_name', '')
        
        logger.info(f"OTP verification attempt for phone: {phone}")
        
        try:
            # Verify OTP
            otp, error = OTP.verify_otp(phone, otp_code)
            
            if error:
                return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if user exists
            user, created = User.objects.get_or_create(
                phone=phone,
                defaults={
                    'username': phone,
                    'role': role,
                    'first_name': first_name,
                    'last_name': last_name,
                }
            )
            
            if not created:
                # Update user info if provided
                if first_name:
                    user.first_name = first_name
                if last_name:
                    user.last_name = last_name
                if role:
                    user.role = role
                user.save()
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            logger.info(f"User authenticated successfully: {user.id}")
            
            return Response({
                'message': 'Authentication successful',
                'user': UserSerializer(user).data,
                'token': str(access_token),
                'refresh': str(refresh),
                'is_new_user': created
            })
            
        except Exception as e:
            logger.error(f"OTP verification failed: {str(e)}")
            return Response(
                {'error': 'Authentication failed'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# User endpoints
class UserViewSet(viewsets.ModelViewSet):
    """
    CRUD for users (admin only, typically).
    """
    queryset = User.objects.all()  # type: ignore[attr-defined]
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]

class MeView(generics.RetrieveAPIView):
    """
    Get current user's profile.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

class UserPreferencesView(generics.UpdateAPIView):
    """
    Update user preferences (accepts array or object, as in Node.js).
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        preferences = request.data
        # Accept both array and object for preferences
        if isinstance(preferences, list):
            user.preferences = preferences
        elif isinstance(preferences, dict):
            user.preferences = preferences
        else:
            return Response({'message': 'Invalid preferences format'}, status=status.HTTP_400_BAD_REQUEST)
        user.save()
        return Response(self.get_serializer(user).data)

class UserLocationView(generics.UpdateAPIView):
    """
    Update user location (accepts lat/lon/address, as in Node.js).
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        latitude = request.data.get('latitude') or request.data.get('lat')
        longitude = request.data.get('longitude') or request.data.get('lon')
        address = request.data.get('address')
        if latitude is not None and longitude is not None:
            from django.contrib.gis.geos import Point
            user.location = Point(float(longitude), float(latitude))
            if address:
                # Optionally store address in preferences or a new field
                user.preferences = user.preferences or {}
                user.preferences['address'] = address
            user.save()
            return Response(self.get_serializer(user).data)
        return Response({'message': 'Latitude and longitude are required'}, status=status.HTTP_400_BAD_REQUEST)

# Business endpoints
class BusinessViewSet(viewsets.ModelViewSet):
    """
    CRUD for businesses. Owner can only access their own.
    """
    serializer_class = BusinessSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only show businesses owned by the user
        return Business.objects.filter(owner_user=self.request.user)  # type: ignore[attr-defined]

    def perform_create(self, serializer):
        business = serializer.save(owner_user=self.request.user)
        # Notify all users who want new_business notifications
        for user in User.objects.filter(role='user'):
            if user_wants_notification(user, 'new_business'):
                Notification.objects.create(
                    user=user,
                    title='New Business Joined!',
                    message=f'{business.name} has joined Minglin. Check out their deals!',
                    notification_type='new_business',
                )
        return business

    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        List businesses owned by the current user (equivalent to getMyBusinesses in Node.js).
        """
        businesses = self.get_queryset()
        return Response(BusinessSerializer(businesses, many=True).data)

    def update(self, request, *args, **kwargs):
        """
        Update business (equivalent to updateBusiness in Node.js).
        """
        business = Business.objects.filter(owner_user=request.user).first()  # type: ignore[attr-defined]
        if not business:
            return Response({'message': 'Business not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Update fields if provided
        if 'name' in request.data:
            business.name = request.data['name']
        if 'description' in request.data:
            business.description = request.data['description']
        if 'contact_phone' in request.data:
            business.contact_phone = request.data['contact_phone']
        
        business.save()
        return Response(BusinessSerializer(business).data)

# Deal endpoints
class DealViewSet(viewsets.ModelViewSet):
    """
    CRUD for deals. Business owner can only access their own deals.
    """
    serializer_class = DealSerializer
    permission_classes = [IsAuthenticated]
    
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        # Show all deals for admin, or only user's business deals
        if self.request.user.is_superuser:
            return Deal.objects.all()  # type: ignore[attr-defined]
        businesses = Business.objects.filter(owner_user=self.request.user)  # type: ignore[attr-defined]
        return Deal.objects.filter(business__in=businesses)  # type: ignore[attr-defined]

    def perform_create(self, serializer):
        # Attach business based on current user if not provided
        if not serializer.validated_data.get('business'):
            businesses = Business.objects.filter(owner_user=self.request.user)  # type: ignore[attr-defined]
            if not businesses.exists():
                logger.error(f"Deal creation failed - no business profile: {self.request.user.id}")
                raise serializers.ValidationError('No business profile found')
            deal = serializer.save(business=businesses.first())
        else:
            deal = serializer.save()
        
        # Try to extract GPS coordinates from image if no location is provided
        if deal.image and not deal.location:
            from .utils import extract_gps_from_image
            lat, lon = extract_gps_from_image(deal.image)
            if lat is not None and lon is not None:
                from django.contrib.gis.geos import Point
                deal.location = Point(lon, lat)  # Note: Point takes (x, y) which is (lon, lat)
                deal.save()
                logger.info(f"GPS coordinates extracted from image for deal {deal.id}: {lat}, {lon}")
        
        logger.info(f"Deal created: {deal.id} by user {self.request.user.id}")
        
        # Send SMS notifications to all customers
        try:
            self.send_deal_notifications(deal)
        except Exception as e:
            logger.error(f"Failed to send deal notifications: {str(e)}")
    
    def send_deal_notifications(self, deal):
        """Send SMS notifications to all customers about the new deal."""
        from .utils import notify
        
        # Get all customer users
        customers = User.objects.filter(role='user')  # type: ignore[attr-defined]
        
        # Create notification message
        business_name = deal.business.name
        deal_title = deal.title
        cta_text = deal.cta if deal.cta else "Visit Store"
        
        customer_message = f"New promotion from {business_name}: {deal_title}. Open your Minglin app for details."
        business_message = f"Promotion notifications sent to {customers.count()} customers"
        
        # Send SMS to each customer
        for customer in customers:
            try:
                if not user_wants_notification(customer, 'new_deal'):
                    continue
                if customer.phone:
                    # Clean phone number (remove + if present, notify function will add 26 prefix)
                    clean_phone = customer.phone
                    if customer.phone.startswith('+'):
                        clean_phone = customer.phone[1:]
                    
                    notify(clean_phone, customer_message)
                    Notification.objects.create(
                        user=customer,
                        title='New Deal!',
                        message=customer_message,
                        notification_type='new_deal',
                        related_deal=deal
                    )
                    notify(deal.business.contact_phone, business_message)
                    logger.info(f"SMS notification sent to {customer.phone} for deal {deal.id}")
            except Exception as e:
                logger.error(f"Failed to send SMS to {customer.phone}: {str(e)}")
        
        logger.info(f"Deal notifications sent to {customers.count()} customers")

    def update(self, request, *args, **kwargs):
        """
        Update deal (equivalent to updateDeal in Node.js).
        """
        deal = self.get_object()
        business = Business.objects.filter(owner_user=request.user).first()  # type: ignore[attr-defined]
        if not business or deal.business != business:
            logger.warning(f"Unauthorized deal update attempt: {deal.id} by user {request.user.id}")
            return Response({'message': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        
        logger.info(f"Deal updated: {deal.id} by user {request.user.id}")
        # Update fields
        for field, value in request.data.items():
            if hasattr(deal, field):
                setattr(deal, field, value)
        deal.save()
        return Response(DealSerializer(deal).data)

    def destroy(self, request, *args, **kwargs):
        """
        Delete deal (equivalent to deleteDeal in Node.js).
        """
        deal = self.get_object()
        business = Business.objects.filter(owner_user=request.user).first()  # type: ignore[attr-defined]
        if not business or deal.business != business:
            logger.warning(f"Unauthorized deal deletion attempt: {deal.id} by user {request.user.id}")
            return Response({'message': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)
        
        logger.info(f"Deal deleted: {deal.id} by user {request.user.id}")
        # Notify users who saved this deal and want deal_removed notifications
        for saved in deal.saved_by.all():
            user = saved.user
            if user_wants_notification(user, 'deal_removed'):
                Notification.objects.create(
                    user=user,
                    title='Deal Removed',
                    message=f'A deal you saved ("{deal.title}") has been removed.',
                    notification_type='deal_removed',
                    related_deal=deal
                )
        deal.delete()
        return Response({'message': 'Deal removed'})

# Public/customer deals endpoint
class CustomerDealsView(generics.ListAPIView):
    """
    List all active deals for customers, with optional location filtering (equivalent to getCustomerDeals in Node.js).
    """
    serializer_class = DealSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        # Get active deals that haven't expired
        queryset = Deal.objects.filter(  # type: ignore[attr-defined]
            is_active=True,
            end_time__gte=timezone.now()
        ).select_related('business')
        
        # Filter by category if provided
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Filter by radius and location if provided
        lat = self.request.query_params.get('lat')
        lon = self.request.query_params.get('lon')
        radius = self.request.query_params.get('radius')
        
        if lat and lon and radius:
            user_location = Point(float(lon), float(lat))
            queryset = queryset.filter(
                location__distance_lte=(user_location, float(radius))
            ).annotate(
                distance=Distance('location', user_location)
            ).order_by('distance')
        
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        logger.debug(f"CustomerDealsView response body: {data}")
        
        # Calculate distances if user has location
        user_lat = request.query_params.get('lat')
        user_lon = request.query_params.get('lon')
        
        if user_lat and user_lon:
            user_location = Point(float(user_lon), float(user_lat))
            for deal_data in data:
                if deal_data.get('location'):
                    deal_location = Point(deal_data['location']['lon'], deal_data['location']['lat'])
                    distance_km = user_location.distance(deal_location) * 111  # Convert to km
                    deal_data['distance'] = round(distance_km, 1)
        
        # Record views for deals (if user is authenticated)
        if request.user.is_authenticated:
            for deal in queryset:
                try:
                    # Check if this user has already viewed this deal to avoid duplicate views
                    existing_view = DealAnalytics.objects.filter(
                        deal=deal,
                        user=request.user,
                        action_type='view'
                    ).first()
                    
                    if not existing_view:
                        # Create analytics record
                        DealAnalytics.objects.create(
                            deal=deal,
                            user=request.user,
                            action_type='view',
                            ip_address=get_client_ip(request),
                            user_agent=request.META.get('HTTP_USER_AGENT', '')
                        )
                        # Update deal views count using F() to avoid race conditions
                        deal.views = F('views') + 1
                        deal.save()
                        # Refresh the deal object to get the updated count
                        deal.refresh_from_db()
                        logger.info(f"View recorded for deal {deal.id} by user {request.user.id}")
                    else:
                        logger.info(f"User {request.user.id} already viewed deal {deal.id}")
                except Exception as e:
                    logger.error(f"Failed to record view for deal {deal.id}: {str(e)}")
        
        return Response(data)

# Public deal detail endpoint
class CustomerDealDetailView(generics.RetrieveAPIView):
    """
    Get individual deal details for customers (public endpoint).
    """
    serializer_class = DealSerializer
    permission_classes = [AllowAny]
    queryset = Deal.objects.filter(is_active=True, end_time__gte=timezone.now())  # type: ignore[attr-defined]

    def retrieve(self, request, *args, **kwargs):
        deal = self.get_object()
        serializer = self.get_serializer(deal)
        data = serializer.data
        
        # Calculate distance if user has location
        user_lat = request.query_params.get('lat')
        user_lon = request.query_params.get('lon')
        
        if user_lat and user_lon and deal.location:
            user_location = Point(float(user_lon), float(user_lat))
            deal_location = Point(deal.location.x, deal.location.y)
            distance_km = user_location.distance(deal_location) * 111  # Convert to km
            data['distance'] = round(distance_km, 1)
        
        # Record view for this specific deal (if user is authenticated)
        if request.user.is_authenticated:
            try:
                # Check if this user has already viewed this deal to avoid duplicate views
                existing_view = DealAnalytics.objects.filter(
                    deal=deal,
                    user=request.user,
                    action_type='view'
                ).first()
                
                if not existing_view:
                    # Create analytics record
                    DealAnalytics.objects.create(
                        deal=deal,
                        user=request.user,
                        action_type='view',
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                    # Update deal views count using F() to avoid race conditions
                    deal.views = F('views') + 1
                    deal.save()
                    # Refresh the deal object to get the updated count
                    deal.refresh_from_db()
                    logger.info(f"View recorded for deal {deal.id} by user {request.user.id}")
                else:
                    logger.info(f"User {request.user.id} already viewed deal {deal.id}")
            except Exception as e:
                logger.error(f"Failed to record view for deal {deal.id}: {str(e)}")
        
        return Response(data)

# My deals endpoint
class MyDealsView(generics.ListAPIView):
    """
    List deals for the current user's business (equivalent to getMyDeals in Node.js).
    """
    serializer_class = DealSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        businesses = Business.objects.filter(owner_user=self.request.user)  # type: ignore[attr-defined]
        return Deal.objects.filter(business__in=businesses)  # type: ignore[attr-defined]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        logger.debug(f"MyDealsView response body: {data}")
        return Response(data)

def custom_exception_handler(exc, context):
    """
    Custom exception handler for better error logging and response formatting.
    """
    # Log the exception with context
    logger.error(
        f"Exception in {context['view'].__class__.__name__}: {str(exc)}",
        exc_info=True,
        extra={
            'view': context['view'].__class__.__name__,
            'request_method': context['request'].method,
            'request_path': context['request'].path,
            'user_id': getattr(context['request'].user, 'id', None),
        }
    )
    
    # Call the default exception handler
    from rest_framework.views import exception_handler
    response = exception_handler(exc, context)
    
    if response is None:
        # Handle unhandled exceptions
        return JsonResponse(
            {'error': 'Internal server error', 'detail': str(exc)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    return response

# Saved Deals endpoints
class SavedDealViewSet(viewsets.ModelViewSet):
    """
    CRUD for saved deals.
    """
    serializer_class = SavedDealSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SavedDeal.objects.filter(user=self.request.user)  # type: ignore[attr-defined]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        # Record analytics
        DealAnalytics.objects.create(
            deal=serializer.instance.deal,
            user=self.request.user,
            action_type='save',
            ip_address=self.get_client_ip(self.request),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )

    def destroy(self, request, *args, **kwargs):
        saved_deal = self.get_object()
        deal = saved_deal.deal
        saved_deal.delete()
        
        # Record analytics
        DealAnalytics.objects.create(
            deal=deal,
            user=request.user,
            action_type='unsave',
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

# Notification endpoints
class NotificationViewSet(viewsets.ModelViewSet):
    """
    CRUD for notifications.
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)  # type: ignore[attr-defined]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['patch'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response(NotificationSerializer(notification).data)

    @action(detail=False, methods=['patch'])
    def mark_all_read(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)  # type: ignore[attr-defined]
        return Response({'message': 'All notifications marked as read'})

# Analytics endpoints
class AnalyticsView(generics.GenericAPIView):
    """
    Analytics endpoint for business owners.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get user's businesses
        businesses = Business.objects.filter(owner_user=request.user)  # type: ignore[attr-defined]
        if not businesses.exists():
            return Response({'message': 'No business found'}, status=status.HTTP_404_NOT_FOUND)

        # Get timeframe from query params
        timeframe = request.query_params.get('timeframe', '7d')
        deal_id = request.query_params.get('dealId')

        # Calculate date range
        now = timezone.now()
        if timeframe == '7d':
            start_date = now - timedelta(days=7)
        elif timeframe == '30d':
            start_date = now - timedelta(days=30)
        elif timeframe == '90d':
            start_date = now - timedelta(days=90)
        else:
            start_date = now - timedelta(days=7)

        # Get deals
        deals = Deal.objects.filter(business__in=businesses)  # type: ignore[attr-defined]
        if deal_id:
            deals = deals.filter(id=deal_id)

        # Get analytics data for the timeframe
        analytics = DealAnalytics.objects.filter(
            deal__in=deals,
            created_at__gte=start_date
        )

        # Calculate stats from analytics table (timeframe-specific)
        timeframe_views = analytics.filter(action_type='view').count()
        timeframe_clicks = analytics.filter(action_type='click').count()
        timeframe_saves = analytics.filter(action_type='save').count()

        # Get current totals from Deal model (all-time)
        total_views = deals.aggregate(total=Sum('views'))['total'] or 0
        total_clicks = deals.aggregate(total=Sum('clicks'))['total'] or 0

        # Deal-specific analytics
        deal_analytics = []
        for deal in deals:
            # Get timeframe-specific analytics
            deal_timeframe_stats = analytics.filter(deal=deal).aggregate(
                views=Count('id', filter=Q(action_type='view')),
                clicks=Count('id', filter=Q(action_type='click')),
                saves=Count('id', filter=Q(action_type='save'))
            )
            
            # Get current totals from Deal model
            deal_current_views = deal.views or 0
            deal_current_clicks = deal.clicks or 0
            
            deal_analytics.append({
                'id': deal.id,
                'title': deal.title,
                'description': deal.description,
                'dealType': deal.category,
                'views': deal_current_views,  # Use current totals
                'clicks': deal_current_clicks,  # Use current totals
                'ctaActions': deal_timeframe_stats['clicks'],  # Use timeframe clicks as CTA actions
                'radiusReach': 5.2,  # Placeholder - would need to calculate from location
                'createdAt': deal.created_at,
                'isActive': deal.is_active,
                'timeframeViews': deal_timeframe_stats['views'],
                'timeframeClicks': deal_timeframe_stats['clicks'],
                'saves': deal_timeframe_stats['saves'],
                'ctr': (deal_current_clicks / deal_current_views * 100) if deal_current_views > 0 else 0
            })

        return Response({
            'timeframe': timeframe,
            'totalViews': total_views,  # All-time totals
            'totalClicks': total_clicks,  # All-time totals
            'timeframeViews': timeframe_views,  # Timeframe-specific
            'timeframeClicks': timeframe_clicks,  # Timeframe-specific
            'totalSaves': timeframe_saves,
            'clickThroughRate': (total_clicks / total_views * 100) if total_views > 0 else 0,
            'conversionRate': (timeframe_saves / timeframe_views * 100) if timeframe_views > 0 else 0,
            'avgRadiusReach': '5.2',  # Placeholder - would need to calculate from location data
            'totalDeals': deals.count(),
            'deals': deal_analytics  # Include deals array for frontend
        })

# Search functionality
class DealSearchView(generics.ListAPIView):
    """
    Search deals by title, description, or category.
    """
    serializer_class = DealSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        query = self.request.query_params.get('q', '')
        if not query:
            return Deal.objects.none()  # type: ignore[attr-defined]

        # Search in title, description, and category
        queryset = Deal.objects.filter(  # type: ignore[attr-defined]
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(category__icontains=query),
            is_active=True,
            end_time__gt=timezone.now()
        ).select_related('business')

        # Apply filters
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)

        # Location filtering
        latitude = self.request.query_params.get('latitude')
        longitude = self.request.query_params.get('longitude')
        max_distance = self.request.query_params.get('max_distance', 10)

        if latitude and longitude:
            try:
                user_location = Point(float(longitude), float(latitude))
                queryset = queryset.filter(
                    location__distance_lte=(user_location, max_distance)
                ).annotate(
                    distance=Distance('location', user_location)
                ).order_by('distance')
            except (ValueError, TypeError):
                pass

        return queryset

# Business logo upload
class BusinessLogoUploadView(generics.UpdateAPIView):
    """
    Upload business logo.
    """
    serializer_class = BusinessSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return Business.objects.filter(owner_user=self.request.user).first()  # type: ignore[attr-defined]

    def update(self, request, *args, **kwargs):
        business = self.get_object()
        if not business:
            return Response({'message': 'Business not found'}, status=status.HTTP_404_NOT_FOUND)

        if 'logo' not in request.FILES:
            return Response({'message': 'No logo file provided'}, status=status.HTTP_400_BAD_REQUEST)

        business.logo = request.FILES['logo']
        business.save()
        
        return Response(BusinessSerializer(business).data)

# Deal interaction tracking
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def record_deal_interaction(request, deal_id):
    """
    Record deal interaction (view, click, etc.).
    """
    try:
        deal = Deal.objects.get(id=deal_id)  # type: ignore[attr-defined]
        action_type = request.data.get('action_type', 'view')
        
        # Check if this user has already performed this action for this deal
        existing_interaction = DealAnalytics.objects.filter(
            deal=deal,
            user=request.user,
            action_type=action_type
        ).first()
        
        if not existing_interaction:
            # Create analytics record
            DealAnalytics.objects.create(
                deal=deal,
                user=request.user,
                action_type=action_type,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Update deal stats using F() to avoid race conditions
            if action_type == 'view':
                deal.views = F('views') + 1
            elif action_type == 'click':
                deal.clicks = F('clicks') + 1
            
            deal.save()
            # Refresh the deal object to get the updated count
            deal.refresh_from_db()
            logger.info(f"{action_type} recorded for deal {deal.id} by user {request.user.id}")
        else:
            logger.info(f"User {request.user.id} already performed {action_type} for deal {deal.id}")

        return Response({
            'message': f'{action_type} recorded successfully',
            'views': deal.views,
            'clicks': deal.clicks,
            'ctr': (deal.clicks / deal.views * 100) if deal.views > 0 else 0
        })
    except Deal.DoesNotExist:  # type: ignore[attr-defined]
        return Response({'message': 'Deal not found'}, status=status.HTTP_404_NOT_FOUND)

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# Add more API views here (auth, users, businesses, deals, etc.)
# See README.md and inline comments for documentation.

# Customer Request endpoints
class CustomerRequestViewSet(viewsets.ModelViewSet):
    """
    CRUD for customer requests (what customers are looking for).
    """
    serializer_class = CustomerRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Customers can see their own requests, businesses can see all active requests
        if self.request.user.role == 'business':
            return CustomerRequest.objects.filter(is_active=True)
        else:
            return CustomerRequest.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        request = serializer.save(user=self.request.user)
        
        # Send notifications to all businesses about the new customer request
        try:
            self.send_request_notifications(request)
        except Exception as e:
            logger.error(f"Failed to send request notifications: {str(e)}")
        
        logger.info(f"Customer request created: {request.id} by user {self.request.user.id}")
    
    def send_request_notifications(self, customer_request):
        """Send SMS notifications to all businesses about the new customer request."""
        from .utils import notify
        
        # Get all business users
        business_users = User.objects.filter(role='business')
        
        # Create notification message
        customer_name = f"{customer_request.user.first_name} {customer_request.user.last_name}".strip() or customer_request.user.phone
        request_title = customer_request.title
        category = customer_request.category or "General"
        
        business_message = f"New customer request: {customer_name} is looking for {request_title} in {category}. Check your Minglin app for details."
        
        # Send SMS to each business
        for business_user in business_users:
            try:
                if business_user.phone:
                    # Clean phone number (remove + if present, notify function will add 26 prefix)
                    clean_phone = business_user.phone
                    if business_user.phone.startswith('+'):
                        clean_phone = business_user.phone[1:]
                    
                    notify(clean_phone, business_message)
                    logger.info(f"Request notification sent to {business_user.phone} for request {customer_request.id}")
            except Exception as e:
                logger.error(f"Failed to send SMS to {business_user.phone}: {str(e)}")
        
        logger.info(f"Request notifications sent to {business_users.count()} businesses")

# Business Request Notifications endpoint
class BusinessRequestNotificationsView(generics.ListAPIView):
    """
    Get customer requests for business owners to see what customers are looking for.
    """
    serializer_class = CustomerRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only business users can access this
        if self.request.user.role != 'business':
            return CustomerRequest.objects.none()
        
        queryset = CustomerRequest.objects.filter(is_active=True)
        
        # Filter by category if provided
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Filter by location and radius if provided
        lat = self.request.query_params.get('lat')
        lon = self.request.query_params.get('lon')
        radius = self.request.query_params.get('radius', 10)  # Default 10km
        
        if lat and lon:
            user_location = Point(float(lon), float(lat))
            queryset = queryset.filter(
                location__distance_lte=(user_location, float(radius))
            ).annotate(
                distance=Distance('location', user_location)
            ).order_by('distance')
        
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        
        # Calculate distances if user has location
        user_lat = request.query_params.get('lat')
        user_lon = request.query_params.get('lon')
        
        if user_lat and user_lon:
            user_location = Point(float(user_lon), float(user_lat))
            for request_data in data:
                if request_data.get('location'):
                    request_location = Point(request_data['location']['lon'], request_data['location']['lat'])
                    distance_km = user_location.distance(request_location) * 111  # Convert to km
                    request_data['distance'] = round(distance_km, 1)
        
        return Response(data)

# Platform Statistics endpoint
class PlatformStatsView(generics.GenericAPIView):
    """
    Get platform statistics for business users.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Only business users can access this
        if request.user.role != 'business':
            return Response({'message': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            # Get total customers (users with role 'user')
            total_customers = User.objects.filter(role='user').count()
            
            # Get total businesses (users with role 'business')
            total_businesses = User.objects.filter(role='business').count()
            
            # Get total active deals
            total_active_deals = Deal.objects.filter(is_active=True, end_time__gte=timezone.now()).count()
            
            # Get total customer requests
            total_customer_requests = CustomerRequest.objects.filter(is_active=True).count()
            
            return Response({
                'total_customers': total_customers,
                'total_businesses': total_businesses,
                'total_active_deals': total_active_deals,
                'total_customer_requests': total_customer_requests,
                'last_updated': timezone.now().isoformat(),
            })
        except Exception as e:
            logger.error(f"Error getting platform stats: {str(e)}")
            return Response(
                {'error': 'Failed to get platform statistics'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# Utility to check user notification preferences

def user_wants_notification(user, notification_type):
    prefs = getattr(user, 'preferences', {})
    if isinstance(prefs, dict):
        notif_prefs = prefs.get('notifications', {})
        # Map notification_type to preference key
        mapping = {
            'new_deal': 'dealAlerts',
            'deal_expiring': 'expiringDeals',
            'deal_expiring_soon': 'expiringDeals',
            'new_business': 'newBusinesses',
            'deal_removed': 'dealAlerts',
        }
        pref_key = mapping.get(notification_type, None)
        if pref_key is not None:
            return notif_prefs.get(pref_key, True)
    return True  # Default to True if not set

class TokenRefreshView(SimpleJWTTokenRefreshView):
    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except get_user_model().DoesNotExist:
            return Response({'detail': 'User not found or inactive.'}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            logger.error(f"Exception in TokenRefreshView: {e}")
            return Response({'detail': 'Token refresh failed.'}, status=status.HTTP_401_UNAUTHORIZED)
