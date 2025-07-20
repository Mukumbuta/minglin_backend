import requests
import logging
from django.conf import settings

logger = logging.getLogger('api')

def notify(phone: str, message: str) -> bool:
    """
    Send SMS notification using Africa's Talking API.
    Returns True if successful, False otherwise.
    """
    try:
        # Africa's Talking API configuration
        api_key = settings.AT_API_KEY if hasattr(settings, 'AT_API_KEY') else 'test_key'
        username = settings.AT_USERNAME if hasattr(settings, 'AT_USERNAME') else 'sandbox'
        
        # Prepare the request
        url = 'https://api.africastalking.com/version1/messaging'
        headers = {
            'ApiKey': api_key,
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        
        # Add country code if not present
        if not phone.startswith('+'):
            phone = '+26' + phone  # Zambia country code
        
        data = {
            'username': username,
            'to': phone,
            'message': message,
            'from': 'Minglin'
        }
        
        # Make the request
        response = requests.post(url, headers=headers, data=data)
        
        if response.status_code == 201:
            logger.info(f"SMS sent successfully to {phone}")
            return True
        else:
            logger.error(f"Failed to send SMS to {phone}: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending SMS to {phone}: {str(e)}")
        return False

def extract_gps_from_image(image_file):
    """
    Extract GPS coordinates from an uploaded image file.
    Returns a tuple of (latitude, longitude) or (None, None) if no GPS data found.
    """
    try:
        from PIL import Image
        from PIL.ExifTags import TAGS, GPSTAGS
        import io
        
        # Open the image
        img = Image.open(image_file)
        
        # Get EXIF data
        exif_data = img._getexif()
        if not exif_data:
            logger.warning("No EXIF data found in image")
            return None, None
        
        # Find GPS info
        gps_info = {}
        for tag_id in exif_data:
            tag = TAGS.get(tag_id, tag_id)
            data = exif_data[tag_id]
            
            if tag == 'GPSInfo':
                for gps_tag_id in data:
                    gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                    gps_info[gps_tag] = data[gps_tag_id]
        
        if not gps_info:
            logger.warning("No GPS data found in image EXIF")
            return None, None
        
        # Extract latitude and longitude
        lat = gps_info.get('GPSLatitude')
        lon = gps_info.get('GPSLongitude')
        lat_ref = gps_info.get('GPSLatitudeRef')
        lon_ref = gps_info.get('GPSLongitudeRef')
        
        if not lat or not lon:
            logger.warning("GPS coordinates not found in image")
            return None, None
        
        # Convert to decimal degrees
        def convert_to_degrees(value):
            """Convert GPS coordinates to decimal degrees."""
            d = float(value[0])
            m = float(value[1])
            s = float(value[2])
            return d + (m / 60.0) + (s / 3600.0)
        
        latitude = convert_to_degrees(lat)
        longitude = convert_to_degrees(lon)
        
        # Apply reference (N/S, E/W)
        if lat_ref == 'S':
            latitude = -latitude
        if lon_ref == 'W':
            longitude = -longitude
        
        logger.info(f"GPS coordinates extracted from image: {latitude}, {longitude}")
        return latitude, longitude
        
    except Exception as e:
        logger.error(f"Error extracting GPS from image: {str(e)}")
        return None, None