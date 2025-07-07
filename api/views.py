from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import authenticate
from .models import User, Business, Deal
from .serializers import RegisterSerializer, UserSerializer, BusinessSerializer, DealSerializer
from rest_framework import viewsets, generics, status, permissions, serializers
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.db.models import Q
import math
from django.utils import timezone
import logging
from django.http import JsonResponse

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

# Auth endpoints
class RegisterView(generics.CreateAPIView):
    """
    User registration endpoint.
    """
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        logger.info(f"User registration attempt: {request.data.get('username', 'unknown')}")
        try:
            response = super().create(request, *args, **kwargs)
            logger.info(f"User registration successful: {response.data.get('id')}")
            return response
        except Exception as e:
            logger.error(f"User registration failed: {str(e)}")
            raise

class LoginView(generics.GenericAPIView):
    """
    User login endpoint. Returns user info and token (to be implemented).
    """
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        logger.info(f"Login attempt: {username}")
        # Placeholder: implement JWT authentication
        user = authenticate(request, username=username, password=request.data.get('password'))
        if user:
            logger.info(f"Login successful: {user.id}")
            return Response(UserSerializer(user).data)
        logger.warning(f"Login failed: {username}")
        return Response({'detail': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

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
        serializer.save(owner_user=self.request.user)

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

    def get_queryset(self):
        # Show all deals for admin, or only user's business deals
        if self.request.user.is_superuser:
            return Deal.objects.all()  # type: ignore[attr-defined]
        businesses = Business.objects.filter(owner_user=self.request.user)  # type: ignore[attr-defined]
        return Deal.objects.filter(business__in=businesses)  # type: ignore[attr-defined]

    def perform_create(self, serializer):
        # Attach business based on current user
        businesses = Business.objects.filter(owner_user=self.request.user)  # type: ignore[attr-defined]
        if not businesses.exists():
            logger.error(f"Deal creation failed - no business profile: {self.request.user.id}")
            raise serializers.ValidationError('No business profile found')
        deal = serializer.save(business=businesses.first())
        logger.info(f"Deal created: {deal.id} by user {self.request.user.id}")

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

# Add more API views here (auth, users, businesses, deals, etc.)
# See README.md and inline comments for documentation.
