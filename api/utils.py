from custom_environs import environment
import requests
import random
import string
import time
import logging
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger('api')

headers = {
    'Content-Type': 'application/json'
}

def notify(phone_number, msg):
    phone_number_format = f'26{phone_number}'
    timestamp = int(time.time() * 1000)
    random_component = random.randint(1000, 9999)
    msg_ref = f'{timestamp}{random_component}'
    
    # Get credentials from environment
    username = os.getenv('PROBASE_USERNAME')
    password = os.getenv('PROBASE_PASSWORD')
    sender_id = os.getenv('PROBASE_SENDER_ID')
    url = os.getenv('PROBASE_URL')
    source = os.getenv('PROBASE_SOURCE')
    
    # Check for specific issues
    if username:
        logger.info(f"Username ends with: '{username[-2:]}' (should be '$$')")
    if password:
        logger.info(f"Password ends with: '{password[-2:]}' (should be '$$')")
    
    # Log credentials for debugging (mask password partially)
    masked_password = f"{password[:4]}***{password[-2:]}" if password and len(password) > 6 else "***"
    logger.info(f"Probase credentials - Username: {username}, Password: {masked_password}, SenderID: {sender_id}, URL: {url}")
  
    payload = {
        "username": username,
        "password": password,
        "recipient": [phone_number_format],
        "senderid": sender_id,
        "message": f'{msg}',
        "source": source,
        "msg_ref": msg_ref
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        results = response.text
        logger.info(f"SMS sent to {phone_number}: {results}")
        logger.info(f"SMS response status code: {response.status_code}")
        return results
    except Exception as e:
        logger.error(f"Error sending SMS to {phone_number}: {str(e)}")
        return None

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