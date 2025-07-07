from rest_framework import serializers
from .models import User, Business, Deal
from django.contrib.gis.geos import Point
from django.contrib.auth.password_validation import validate_password

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'role', 'phone', 'password', 'password2',
            'preferences', 'location', 'notifications_push', 'first_name', 'last_name'
        ]
        extra_kwargs = {'password': {'write_only': True}, 'password2': {'write_only': True}}

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password': "Passwords don't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'role', 'phone', 'preferences',
            'location', 'notifications_push', 'first_name', 'last_name'
        ]
        read_only_fields = ['id', 'username', 'email']

class BusinessSerializer(serializers.ModelSerializer):
    owner_user = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = Business
        fields = ['id', 'name', 'description', 'contact_phone', 'owner_user']
        read_only_fields = ['id', 'owner_user']

class DealSerializer(serializers.ModelSerializer):
    business = BusinessSerializer(read_only=True)
    business_id = serializers.PrimaryKeyRelatedField(
        queryset=Business.objects.all(), source='business', write_only=True
    )
    location = serializers.SerializerMethodField()
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Deal
        fields = [
            'id', 'business', 'business_id', 'title', 'description', 'image',
            'category', 'cta', 'start_time', 'end_time', 'location',
            'is_active', 'views', 'clicks', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'business', 'views', 'clicks', 'created_at', 'updated_at']

    def get_location(self, obj):
        if obj.location:
            return {'lat': obj.location.y, 'lon': obj.location.x}
        return None

    def to_internal_value(self, data):
        # Accept lat/lon as input for location
        ret = super().to_internal_value(data)
        lat = data.get('latitude') or data.get('lat')
        lon = data.get('longitude') or data.get('lon')
        if lat is not None and lon is not None:
            ret['location'] = Point(float(lon), float(lat))
        return ret

# See README.md and inline comments for documentation. 