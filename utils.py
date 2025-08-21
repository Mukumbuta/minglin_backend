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
    
    username = os.getenv('PROBASE_USERNAME')
    password = os.getenv('PROBASE_PASSWORD')
    sender_id = os.getenv('PROBASE_SENDER_ID')
    url = os.getenv('PROBASE_URL')
    source = os.getenv('PROBASE_SOURCE')
    
    # Detailed debugging - show exact characters
    logger.info(f"[ROOT UTILS] Raw environment variables:")
    logger.info(f"  PROBASE_USERNAME length: {len(username) if username else 'None'}, value: '{username}'")
    logger.info(f"  PROBASE_PASSWORD length: {len(password) if password else 'None'}, ends with: '{password[-4:] if password else 'None'}'")
    logger.info(f"  PROBASE_SENDER_ID: '{sender_id}'")
    logger.info(f"  PROBASE_URL: '{url}'")
    logger.info(f"  PROBASE_SOURCE: '{source}'")
    
    # Check for specific issues
    if username:
        logger.info(f"Username ends with: '{username[-2:]}' (should be '$$')")
    if password:
        logger.info(f"Password ends with: '{password[-2:]}' (should be '$$')")
  
    payload = {
        'username': username,
        'password': password,
        'senderid': sender_id,
        'source': source,
        'recipient': [phone_number_format],
        'message': f'{msg}',
        'msg_ref': msg_ref,
    }
    
    # Log the full payload (except password) for debugging
    debug_payload = payload.copy()
    debug_payload['password'] = f"{password[:4]}***{password[-2:]}" if password and len(password) > 6 else "***"
    logger.info(f"[ROOT UTILS] SMS payload: {debug_payload}")

    try:
        response = requests.post(url, json=payload, headers=headers)
        results = response.text
        logger.info(f"[ROOT UTILS] SMS sent to {phone_number}: {results}")
        logger.info(f"[ROOT UTILS] SMS response status code: {response.status_code}")
        print(results)  # Keep original print for compatibility
        return results
    except Exception as e:
        logger.error(f"[ROOT UTILS] Error sending SMS to {phone_number}: {str(e)}")
        print(str(e))  # Keep original print for compatibility
        return None