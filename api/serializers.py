from rest_framework import serializers
from .models import User, Business, Deal, SavedDeal, Notification, DealAnalytics, OTP, CustomerRequest
from django.contrib.gis.geos import Point
from django.contrib.auth.password_validation import validate_password

class PhoneAuthSerializer(serializers.Serializer):
    """
    Serializer for phone number authentication (login/register).
    """
    phone = serializers.CharField(max_length=32)
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, required=False)

class OTPVerificationSerializer(serializers.Serializer):
    """
    Serializer for OTP verification.
    """
    phone = serializers.CharField(max_length=32)
    otp_code = serializers.CharField(max_length=6)
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, required=False)
    first_name = serializers.CharField(max_length=30, required=False)
    last_name = serializers.CharField(max_length=30, required=False)

class RegisterSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(max_length=32)
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES)

    class Meta:
        model = User
        fields = [
            'id', 'phone', 'role', 'first_name', 'last_name',
            'preferences', 'location', 'notifications_push'
        ]
        read_only_fields = ['id']

    def validate_phone(self, value):
        """
        Check that the phone number is unique.
        """
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("A user with this phone number already exists.")
        return value

    def create(self, validated_data):
        # Create user with phone as username
        validated_data['username'] = validated_data['phone']
        user = User(**validated_data)
        user.save()
        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'phone', 'role', 'preferences',
            'location', 'notifications_push', 'first_name', 'last_name'
        ]
        read_only_fields = ['id', 'phone']

class BusinessSerializer(serializers.ModelSerializer):
    owner_user = serializers.PrimaryKeyRelatedField(read_only=True)
    logo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Business
        fields = ['id', 'name', 'description', 'contact_phone', 'logo', 'logo_url', 'owner_user']
        read_only_fields = ['id', 'owner_user']

    def get_logo_url(self, obj):
        if obj.logo:
            return self.context['request'].build_absolute_uri(obj.logo.url)
        return None

class DealSerializer(serializers.ModelSerializer):
    business = BusinessSerializer(read_only=True)
    business_id = serializers.PrimaryKeyRelatedField(
        queryset=Business.objects.all(), source='business', write_only=True, required=False
    )
    location = serializers.SerializerMethodField()
    image = serializers.ImageField(required=False, allow_null=True, max_length=None)
    image_url = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()

    class Meta:
        model = Deal
        fields = [
            'id', 'business', 'business_id', 'title', 'description', 'image', 'image_url',
            'category', 'cta', 'start_time', 'end_time', 'location',
            'is_active', 'views', 'clicks', 'created_at', 'updated_at', 'is_saved'
        ]
        read_only_fields = ['id', 'business', 'views', 'clicks', 'created_at', 'updated_at']

    def get_location(self, obj):
        if obj.location:
            return {'lat': obj.location.y, 'lon': obj.location.x}
        return None

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None

    def get_is_saved(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.saved_by.filter(user=request.user).exists()
        return False

    def to_internal_value(self, data):
        # Accept lat/lon as input for location
        ret = super().to_internal_value(data)
        lat = data.get('latitude') or data.get('lat')
        lon = data.get('longitude') or data.get('lon')
        if lat is not None and lon is not None:
            ret['location'] = Point(float(lon), float(lat))
        
        # Handle field name mapping from React Native
        if 'isActive' in data:
            # Convert string boolean to Python boolean
            is_active_value = data['isActive']
            if isinstance(is_active_value, str):
                ret['is_active'] = is_active_value.lower() == 'true'
            else:
                ret['is_active'] = bool(is_active_value)
        # Don't map imageUrl to image field - handle separately
        if 'imageUrl' in data:
            # Remove imageUrl from data since we'll handle it separately
            data.pop('imageUrl', None)
            
        return ret

class SavedDealSerializer(serializers.ModelSerializer):
    deal = DealSerializer(read_only=True)
    deal_id = serializers.PrimaryKeyRelatedField(
        queryset=Deal.objects.all(), source='deal', write_only=True
    )

    class Meta:
        model = SavedDeal
        fields = ['id', 'deal', 'deal_id', 'saved_at']
        read_only_fields = ['id', 'saved_at']

class NotificationSerializer(serializers.ModelSerializer):
    related_deal = DealSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'message', 'notification_type', 'is_read',
            'related_deal', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class DealAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DealAnalytics
        fields = [
            'id', 'deal', 'user', 'action_type', 'ip_address',
            'user_agent', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class CustomerRequestSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    location = serializers.SerializerMethodField()
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = CustomerRequest
        fields = [
            'id', 'user', 'user_name', 'title', 'description', 'category',
            'location', 'budget_min', 'budget_max', 'urgency', 'created_at',
            'is_active', 'expires_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']

    def get_location(self, obj):
        if obj.location:
            return {'lat': obj.location.y, 'lon': obj.location.x}
        return None

    def get_user_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.phone

    def to_internal_value(self, data):
        # Accept lat/lon as input for location
        ret = super().to_internal_value(data)
        lat = data.get('latitude') or data.get('lat')
        lon = data.get('longitude') or data.get('lon')
        if lat is not None and lon is not None:
            ret['location'] = Point(float(lon), float(lat))
        return ret

# See README.md and inline comments for documentation. 